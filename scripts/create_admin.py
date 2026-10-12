"""
CLI Script to create or promote an admin user in MiniCloud.
Usage:
  python scripts/create_admin.py --username admin --email admin@minicloud.lan --password AdminSecret123
"""
import sys
import os
import argparse
from werkzeug.security import generate_password_hash

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from app.config import Config
from app.database import get_db, init_db
from app.storage import get_storage_backend

def create_admin(username, email, password):
    db_path = Config.DATABASE_PATH
    init_db(db_path)
    conn = get_db(db_path)
    cursor = conn.cursor()

    # Check if username or email already exists
    cursor.execute("SELECT id, role FROM users WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE;", (username, email))
    existing = cursor.fetchone()

    password_hash = generate_password_hash(password)

    if existing:
        print(f"User '{username}' already exists. Promoting to 'admin' role and updating password...")
        with conn:
            conn.execute(
                "UPDATE users SET role = 'admin', password_hash = ? WHERE id = ?;",
                (password_hash, existing["id"])
            )
        user_id = existing["id"]
        print(f"[SUCCESS] User '{username}' (ID: {user_id}) promoted to admin.")
    else:
        print(f"Creating new administrator account '{username}'...")
        with conn:
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, role, storage_quota_mb)
                VALUES (?, ?, ?, 'admin', ?);
                """,
                (username, email, password_hash, Config.USER_STORAGE_QUOTA_MB)
            )
            user_id = cursor.lastrowid
        print(f"[SUCCESS] Admin account created with ID {user_id}.")

    # Provision user folder in storage
    storage = get_storage_backend(
        backend_type=Config.STORAGE_BACKEND,
        namenode_host=Config.HDFS_NAMENODE_HOST,
        webhdfs_port=Config.HDFS_WEBHDFS_PORT,
        base_path=Config.HDFS_BASE_PATH,
        hdfs_user=Config.HDFS_USER,
        mock_dir=Config.MOCK_STORAGE_DIR
    )
    user_dir = f"users/{user_id}/files"
    try:
        storage.ensure_dir(user_dir)
        print(f"Provisioned storage directory '{user_dir}'.")
    except Exception as e:
        print(f"Note: Could not create storage directory: {e}")

    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Create MiniCloud Admin User")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--email", default="admin@minicloud.lan", help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password (min 8 characters)")
    args = parser.parse_args()

    if len(args.password) < 8:
        print("[ERROR] Password must be at least 8 characters.")
        sys.exit(1)

    create_admin(args.username, args.email, args.password)

if __name__ == "__main__":
    main()
