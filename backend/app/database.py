"""
Database module for MiniCloud.
Provides SQLite database connection management, WAL mode activation, foreign key enforcement,
and automated schema initialization.
"""
import sqlite3
import os
import logging
from flask import g, current_app

logger = logging.getLogger("minicloud.database")

SCHEMA_SQL = """
-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT COLLATE NOCASE NOT NULL UNIQUE,
    email TEXT COLLATE NOCASE NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'user')) DEFAULT 'user',
    storage_quota_mb INTEGER NOT NULL DEFAULT 1024,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Virtual Folders Table
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    parent_folder_id INTEGER,
    folder_name TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- Partial Unique Index: prevent duplicate active folder names in the same directory for a user
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_folder 
ON folders(user_id, IFNULL(parent_folder_id, -1), folder_name) 
WHERE is_deleted = 0;

-- 3. Files Table
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    folder_id INTEGER,
    original_name TEXT NOT NULL,
    stored_name TEXT NOT NULL UNIQUE,
    hdfs_path TEXT NOT NULL UNIQUE,
    file_size INTEGER NOT NULL DEFAULT 0,
    mime_type TEXT DEFAULT 'application/octet-stream',
    extension TEXT,
    sha256 TEXT,
    status TEXT NOT NULL CHECK(status IN ('pending', 'ready')) DEFAULT 'pending',
    is_starred INTEGER NOT NULL DEFAULT 0,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TIMESTAMP,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_files_user_folder_deleted ON files(user_id, folder_id, is_deleted);
CREATE INDEX IF NOT EXISTS idx_files_user_starred ON files(user_id, is_starred);
CREATE INDEX IF NOT EXISTS idx_files_user_accessed ON files(user_id, last_accessed_at);
CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);

-- 4. JWT Token Blocklist Table
CREATE TABLE IF NOT EXISTS token_blocklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jti TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_token_blocklist_jti ON token_blocklist(jti);
"""

def get_db(db_path: str = None) -> sqlite3.Connection:
    """
    Returns the current SQLite database connection for the Flask request context.
    If outside request context, creates a direct connection.
    """
    target_path = db_path or current_app.config.get("DATABASE_PATH") if current_app else db_path
    if not target_path:
        raise ValueError("Database path not specified")

    # In Flask request context
    if current_app:
        if 'db' not in g:
            conn = sqlite3.connect(
                target_path,
                detect_types=sqlite3.PARSE_DECLTYPES,
                timeout=20.0
            )
            # Enable WAL mode and foreign keys
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.row_factory = sqlite3.Row
            g.db = conn
        return g.db
    
    # Standalone script execution
    conn = sqlite3.connect(
        target_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
        timeout=20.0
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn

def close_db(e=None):
    """Closes connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(db_path: str):
    """Initializes tables and indexes from SCHEMA_SQL."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = get_db(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)
    logger.info("Initialized MiniCloud database at: %s", db_path)
    if not current_app:
        conn.close()
