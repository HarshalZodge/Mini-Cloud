"""
Configuration module for MiniCloud.
Loads configuration from environment variables or .env file with solid defaults.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env file if available
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

class Config:
    # Flask & Security
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default-flask-secret-key-replace-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-jwt-secret-key-replace-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "60")))
    
    # Server
    HOST = os.getenv("APP_HOST", "0.0.0.0")
    PORT = int(os.getenv("APP_PORT", "5000"))
    
    # CORS
    raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    CORS_ORIGINS = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./minicloud.db")
    if not os.path.isabs(DATABASE_PATH):
        # Resolve relative to backend folder
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATABASE_PATH = os.path.abspath(os.path.join(backend_root, DATABASE_PATH))

    # Storage Backend
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "mock").lower()
    HDFS_NAMENODE_HOST = os.getenv("HDFS_NAMENODE_HOST", "127.0.0.1")
    HDFS_WEBHDFS_PORT = int(os.getenv("HDFS_WEBHDFS_PORT", "9870"))
    HDFS_BASE_PATH = os.getenv("HDFS_BASE_PATH", "/minicloud")
    HDFS_USER = os.getenv("HDFS_USER", "hadoop")
    HDFS_REPLICATION_FACTOR = int(os.getenv("HDFS_REPLICATION_FACTOR", "1"))
    HDFS_DEFAULT_BLOCK_SIZE = int(os.getenv("HDFS_DEFAULT_BLOCK_SIZE", "134217728")) # 128 MB
    HDFS_REQUEST_TIMEOUT_SECONDS = int(os.getenv("HDFS_REQUEST_TIMEOUT_SECONDS", "30"))
    MOCK_STORAGE_DIR = os.getenv("MOCK_STORAGE_DIR", "./mock_storage")
    if not os.path.isabs(MOCK_STORAGE_DIR):
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        MOCK_STORAGE_DIR = os.path.abspath(os.path.join(backend_root, MOCK_STORAGE_DIR))

    # Limits and Quotas
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024 # Flask max payload
    USER_STORAGE_QUOTA_MB = int(os.getenv("USER_STORAGE_QUOTA_MB", "1024"))
    
    # Security: File Extension restrictions
    raw_blocked = os.getenv("BLOCKED_EXTENSIONS", ".exe,.bat,.cmd,.sh,.js,.msi")
    BLOCKED_EXTENSIONS = {ext.strip().lower() for ext in raw_blocked.split(",") if ext.strip()}

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
