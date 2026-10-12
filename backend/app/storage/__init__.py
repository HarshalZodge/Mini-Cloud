"""
Storage factory and public interfaces
"""
from typing import Optional
from app.storage.base import (
    StorageBackend,
    StorageError,
    StorageUnavailableError,
    StorageNotFoundError
)
from app.storage.hdfs import HdfsStorage
from app.storage.mock import MockStorage

_storage_instance: Optional[StorageBackend] = None

def get_storage_backend(
    backend_type: str = "mock",
    namenode_host: str = "localhost",
    webhdfs_port: int = 9870,
    base_path: str = "/minicloud",
    hdfs_user: str = "hadoop",
    replication_factor: int = 1,
    default_block_size: int = 134217728,
    timeout_seconds: int = 30,
    mock_dir: str = "./mock_storage"
) -> StorageBackend:
    """
    Factory function returning the active StorageBackend singleton or instance.
    """
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    if backend_type.lower() == "hdfs":
        _storage_instance = HdfsStorage(
            namenode_host=namenode_host,
            webhdfs_port=webhdfs_port,
            base_path=base_path,
            hdfs_user=hdfs_user,
            replication_factor=replication_factor,
            default_block_size=default_block_size,
            timeout_seconds=timeout_seconds
        )
    else:
        _storage_instance = MockStorage(base_dir=mock_dir)

    return _storage_instance

def reset_storage_backend():
    """Resets the storage singleton (primarily for testing purposes)."""
    global _storage_instance
    _storage_instance = None

__all__ = [
    "StorageBackend",
    "StorageError",
    "StorageUnavailableError",
    "StorageNotFoundError",
    "HdfsStorage",
    "MockStorage",
    "get_storage_backend",
    "reset_storage_backend"
]
