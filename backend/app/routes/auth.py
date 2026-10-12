"""
Authentication routes for MiniCloud:
  - Register: Creates user; first registered user becomes 'admin', subsequent 'user'.
  - Login: Validates credentials, creates JWT token.
  - Logout: Revokes JWT by recording jti in token_blocklist.
  - Me: Returns authenticated user profile and quota.
  - Change Password: Updates password after verifying old password.
"""
import re
from datetime import datetime, timezone
from flask import Blueprint, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)

from app.database import get_db
from app.utils.response import api_success, api_error
from app.storage import get_storage_backend

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_\.-]{3,30}$")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Validation
    if not USERNAME_REGEX.match(username):
        return api_error("INVALID_USERNAME", "Username must be 3-30 characters and alphanumeric (dot, underscore, dash allowed).")

    if not EMAIL_REGEX.match(email):
        return api_error("INVALID_EMAIL", "Please provide a valid email address.")

    if len(password) < 8:
        return api_error("PASSWORD_TOO_SHORT", "Password must be at least 8 characters long.")

    conn = get_db()
    cursor = conn.cursor()

    # Check for existing user
    cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE;", (username, email))
    if cursor.fetchone():
        return api_error("USER_ALREADY_EXISTS", "Username or email is already registered.", status_code=409)

    # First user check -> role='admin', else 'user'
    cursor.execute("SELECT COUNT(*) AS count FROM users;")
    user_count = cursor.fetchone()["count"]
    assigned_role = "admin" if user_count == 0 else "user"

    password_hash = generate_password_hash(password)
    quota_mb = current_app.config.get("USER_STORAGE_QUOTA_MB", 1024)

    try:
        with conn:
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, role, storage_quota_mb)
                VALUES (?, ?, ?, ?, ?);
                """,
                (username, email, password_hash, assigned_role, quota_mb)
            )
            user_id = cursor.lastrowid

            # Provision personal user HDFS storage folder: /minicloud/users/{user_id}/files
            storage = get_storage_backend(
                backend_type=current_app.config["STORAGE_BACKEND"],
                namenode_host=current_app.config["HDFS_NAMENODE_HOST"],
                webhdfs_port=current_app.config["HDFS_WEBHDFS_PORT"],
                base_path=current_app.config["HDFS_BASE_PATH"],
                hdfs_user=current_app.config["HDFS_USER"],
                mock_dir=current_app.config["MOCK_STORAGE_DIR"]
            )
            user_dir = f"users/{user_id}/files"
            try:
                storage.ensure_dir(user_dir)
            except Exception as e:
                current_app.logger.warning("Could not pre-provision storage folder for user %d: %s", user_id, str(e))

    except Exception as e:
        current_app.logger.error("Registration error: %s", str(e))
        return api_error("DATABASE_ERROR", "Failed to register user.", status_code=500)

    # Auto login on registration
    access_token = create_access_token(
        identity=str(user_id),
        additional_claims={"role": assigned_role, "username": username}
    )

    return api_success({
        "token": access_token,
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
            "role": assigned_role,
            "storageQuotaMb": quota_mb
        }
    }, status_code=201)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("identifier") or data.get("username") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return api_error("MISSING_CREDENTIALS", "Username/email and password are required.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE;",
        (identifier, identifier.lower())
    )
    user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return api_error("INVALID_CREDENTIALS", "Invalid username or password.", status_code=401)

    access_token = create_access_token(
        identity=str(user["id"]),
        additional_claims={"role": user["role"], "username": user["username"]}
    )

    return api_success({
        "token": access_token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "storageQuotaMb": user["storage_quota_mb"],
            "createdAt": user["created_at"]
        }
    })

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """Revokes token by placing its JTI into token_blocklist."""
    jwt_data = get_jwt()
    jti = jwt_data.get("jti")
    exp = jwt_data.get("exp")
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    try:
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO token_blocklist (jti, expires_at) VALUES (?, ?);",
                (jti, expires_at)
            )
        return api_success({"message": "Successfully logged out."})
    except Exception as e:
        current_app.logger.error("Logout failure: %s", str(e))
        return api_error("LOGOUT_ERROR", "Could not complete logout.", status_code=500)

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role, storage_quota_mb, created_at FROM users WHERE id = ?;", (user_id,))
    user = cursor.fetchone()

    if not user:
        return api_error("USER_NOT_FOUND", "User record no longer exists.", status_code=404)

    # Compute current used storage
    cursor.execute(
        "SELECT IFNULL(SUM(file_size), 0) AS used_bytes, COUNT(id) AS file_count FROM files WHERE user_id = ? AND status = 'ready';",
        (user_id,)
    )
    storage_stats = cursor.fetchone()
    used_bytes = storage_stats["used_bytes"]
    used_mb = round(used_bytes / (1024 * 1024), 2)

    return api_success({
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "storageQuotaMb": user["storage_quota_mb"],
        "storageUsedBytes": used_bytes,
        "storageUsedMb": used_mb,
        "fileCount": storage_stats["file_count"],
        "createdAt": user["created_at"]
    })

@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    current_password = data.get("currentPassword") or ""
    new_password = data.get("newPassword") or ""

    if len(new_password) < 8:
        return api_error("PASSWORD_TOO_SHORT", "New password must be at least 8 characters long.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?;", (user_id,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], current_password):
        return api_error("INVALID_PASSWORD", "Current password is incorrect.", status_code=400)

    new_hash = generate_password_hash(new_password)
    with conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?;", (new_hash, user_id))

    return api_success({"message": "Password changed successfully."})
