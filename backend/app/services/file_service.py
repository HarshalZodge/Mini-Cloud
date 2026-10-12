"""
File service managing business logic and consistency protocol:
  - Upload protocol with atomic rollbacks
  - Quota verification (before and after upload)
  - Filename sanitization and collision auto-renaming
  - Extension filtering
  - Download token creation and verification
  - Storage deletion consistency
"""
import os
import uuid
import hashlib
import mimetypes
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
import jwt
from flask import current_app

from app.database import get_db
from app.storage import get_storage_backend, StorageError
from app.storage.base import StorageNotFoundError

logger = logging.getLogger("minicloud.file_service")

# File category classifier for analytics
CATEGORY_MAPPINGS = {
    "image": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"],
    "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".xls", ".xlsx", ".csv", ".ppt", ".pptx"],
    "media": [".mp4", ".mkv", ".mp3", ".wav", ".avi", ".mov", ".flac", ".ogg", ".webm"],
    "archive": [".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz"],
    "code": [".py", ".java", ".c", ".cpp", ".h", ".html", ".css", ".json", ".xml", ".sql", ".sh", ".yaml", ".yml"]
}

def get_file_category(extension: str) -> str:
    ext = (extension or "").lower()
    for category, extensions in CATEGORY_MAPPINGS.items():
        if ext in extensions:
            return category
    return "other"

def sanitize_filename(filename: str) -> str:
    """Sanitizes filename, removing directory separators and control characters."""
    clean = os.path.basename(filename).strip()
    clean = "".join(c for c in clean if c not in '<>:"/\\|?*\0')
    if not clean:
        clean = "unnamed_file"
    return clean[:255]

def get_unique_filename(conn, user_id: int, folder_id: Optional[int], filename: str) -> str:
    """
    If a file with the same original_name already exists in this folder for the user,
    auto-renames it with a suffix e.g. 'document (1).pdf'.
    """
    base, ext = os.path.splitext(filename)
    cursor = conn.cursor()
    
    query = """
    SELECT original_name FROM files 
    WHERE user_id = ? AND IFNULL(folder_id, -1) = IFNULL(?, -1) AND is_deleted = 0;
    """
    cursor.execute(query, (user_id, folder_id))
    existing_names = {row["original_name"].lower() for row in cursor.fetchall()}

    if filename.lower() not in existing_names:
        return filename

    counter = 1
    while True:
        candidate = f"{base} ({counter}){ext}"
        if candidate.lower() not in existing_names:
            return candidate
        counter += 1

def check_user_quota(user_id: int, additional_bytes: int) -> Tuple[bool, int, int]:
    """
    Calculates used space (sum of ready file sizes, including Trash) + additional_bytes.
    Returns (within_quota: bool, used_bytes: int, quota_bytes: int).
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT storage_quota_mb FROM users WHERE id = ?;", (user_id,))
    user = cursor.fetchone()
    if not user:
        return False, 0, 0

    quota_bytes = user["storage_quota_mb"] * 1024 * 1024

    cursor.execute(
        "SELECT IFNULL(SUM(file_size), 0) AS used FROM files WHERE user_id = ? AND status = 'ready';",
        (user_id,)
    )
    used_bytes = cursor.fetchone()["used"]

    if (used_bytes + additional_bytes) > quota_bytes:
        return False, used_bytes, quota_bytes
    return True, used_bytes, quota_bytes

def generate_download_token(user_id: int, file_id: int) -> str:
    """Generates a 60-second single-purpose signed JWT for secure browser downloads."""
    payload = {
        "sub": str(user_id),
        "file_id": file_id,
        "purpose": "download",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=60)
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")

def verify_download_token(token: str, file_id: int) -> Optional[int]:
    """Verifies download token and returns user_id if valid."""
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        if payload.get("purpose") != "download" or payload.get("file_id") != file_id:
            return None
        return int(payload.get("sub"))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def execute_upload_consistency_protocol(user_id: int, folder_id: Optional[int], file_stream, original_name: str, file_size: int) -> Dict[str, Any]:
    """
    Executes the 6-step consistency protocol per Section 5:
    1. Validation (extension, folder ownership, quota).
    2. Insert files row with status='pending'.
    3. Stream bytes to HDFS / MockStorage.
    4. Verify uploaded length via stat().
    5. Update row to status='ready' with SHA-256.
    6. Rollback on ANY failure (delete partial storage, remove pending DB row).
    """
    conn = get_db()
    cursor = conn.cursor()

    # 1. Validation
    safe_name = sanitize_filename(original_name)
    base_name, extension = os.path.splitext(safe_name)
    ext_lower = extension.lower()

    if ext_lower in current_app.config.get("BLOCKED_EXTENSIONS", set()):
        raise ValueError(f"File extension '{ext_lower}' is blocked for security reasons.")

    if folder_id is not None:
        cursor.execute("SELECT id FROM folders WHERE id = ? AND user_id = ? AND is_deleted = 0;", (folder_id, user_id))
        if not cursor.fetchone():
            raise ValueError("Target folder does not exist or has been deleted.")

    # Pre-upload quota check
    ok, used, quota = check_user_quota(user_id, file_size)
    if not ok:
        raise PermissionError(f"Storage quota exceeded. Free space remaining: {round((quota - used) / (1024*1024), 2)} MB.")

    final_name = get_unique_filename(conn, user_id, folder_id, safe_name)
    file_uuid = uuid.uuid4().hex
    stored_name = f"{file_uuid}{extension}"
    # HDFS path format: users/{user_id}/files/{stored_name}
    relative_storage_path = f"users/{user_id}/files/{stored_name}"

    mime_type, _ = mimetypes.guess_type(final_name)
    if not mime_type:
        mime_type = "application/octet-stream"

    # 2. Insert pending record
    with conn:
        cursor.execute(
            """
            INSERT INTO files (
                user_id, folder_id, original_name, stored_name, hdfs_path,
                file_size, mime_type, extension, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending');
            """,
            (user_id, folder_id, final_name, stored_name, relative_storage_path, file_size, mime_type, ext_lower)
        )
        file_id = cursor.lastrowid

    storage = get_storage_backend(
        backend_type=current_app.config["STORAGE_BACKEND"],
        namenode_host=current_app.config["HDFS_NAMENODE_HOST"],
        webhdfs_port=current_app.config["HDFS_WEBHDFS_PORT"],
        base_path=current_app.config["HDFS_BASE_PATH"],
        hdfs_user=current_app.config["HDFS_USER"],
        mock_dir=current_app.config["MOCK_STORAGE_DIR"]
    )

    # 3. Stream bytes & compute hash simultaneously
    sha256 = hashlib.sha256()
    bytes_uploaded = 0

    class HashingStreamWrapper:
        def __init__(self, stream):
            self.stream = stream

        def read(self, chunk_size=65536):
            chunk = self.stream.read(chunk_size)
            if chunk:
                sha256.update(chunk)
                nonlocal bytes_uploaded
                bytes_uploaded += len(chunk)
            return chunk

    wrapped_stream = HashingStreamWrapper(file_stream)

    try:
        storage.upload(relative_storage_path, wrapped_stream, file_size)

        # 4. Verify length via stat
        stat_info = storage.stat(relative_storage_path)
        reported_len = stat_info.get("length", 0)
        if reported_len != file_size:
            raise StorageError(f"Size verification failed. Expected {file_size}, storage reported {reported_len}.")

        digest = sha256.hexdigest()

        # 5. Mark as ready
        with conn:
            conn.execute(
                """
                UPDATE files 
                SET status = 'ready', file_size = ?, sha256 = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (file_size, digest, file_id)
            )

        cursor.execute("SELECT * FROM files WHERE id = ?;", (file_id,))
        return dict(cursor.fetchone())

    except Exception as exc:
        logger.error("Upload failure for file %d (%s): %s. Executing rollback.", file_id, safe_name, str(exc))
        # 6. Rollback
        try:
            storage.delete(relative_storage_path)
        except Exception as e:
            logger.warning("Cleanup of partial storage object '%s' failed: %s", relative_storage_path, str(e))

        with conn:
            conn.execute("DELETE FROM files WHERE id = ?;", (file_id,))

        raise exc

def execute_permanent_file_delete(user_id: int, file_id: int) -> bool:
    """
    Permanent deletion: deletes physical storage file first.
    If storage delete succeeds (or already missing), removes SQLite row.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id = ? AND user_id = ?;", (file_id, user_id))
    file_record = cursor.fetchone()

    if not file_record:
        return False

    storage = get_storage_backend(
        backend_type=current_app.config["STORAGE_BACKEND"],
        namenode_host=current_app.config["HDFS_NAMENODE_HOST"],
        webhdfs_port=current_app.config["HDFS_WEBHDFS_PORT"],
        base_path=current_app.config["HDFS_BASE_PATH"],
        hdfs_user=current_app.config["HDFS_USER"],
        mock_dir=current_app.config["MOCK_STORAGE_DIR"]
    )

    hdfs_path = file_record["hdfs_path"]
    try:
        storage.delete(hdfs_path)
    except StorageNotFoundError:
        pass # Already gone
    except Exception as exc:
        logger.error("Failed to delete physical file %s: %s", hdfs_path, str(exc))
        raise StorageError(f"Failed to delete file from storage: {str(exc)}")

    with conn:
        conn.execute("DELETE FROM files WHERE id = ?;", (file_id,))

    return True
