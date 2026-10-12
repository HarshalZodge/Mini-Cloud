"""
Storage abstraction module for MiniCloud.
Provides base interface and concrete implementations for WebHDFS and Mock filesystem.
"""
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional

class StorageError(Exception):
    """Base exception for storage backend errors."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class StorageUnavailableError(StorageError):
    """Raised when the storage service is completely unreachable (e.g. HDFS down)."""
    def __init__(self, message: str = "Storage engine is unreachable", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, details=details)

class StorageNotFoundError(StorageError):
    """Raised when an object or file does not exist in storage."""
    def __init__(self, message: str = "File not found in storage", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)


class StorageBackend(ABC):
    """
    Abstract interface for MiniCloud storage operations.
    All storage engines (HdfsStorage, MockStorage) must strictly implement this interface.
    """

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """
        Check health of the storage backend.
        Returns a dictionary containing health status details.
        """
        pass

    @abstractmethod
    def ensure_dir(self, path: str) -> bool:
        """
        Ensure that directory exists at path (equivalent to mkdir -p).
        """
        pass

    @abstractmethod
    def upload(self, path: str, stream: Any, size: int) -> Dict[str, Any]:
        """
        Uploads content from a file-like stream or bytes to the given path.
        Returns dict with file attributes like 'size' and 'path'.
        """
        pass

    @abstractmethod
    def download(self, path: str, chunk_size: int = 1048576) -> Iterator[bytes]:
        """
        Returns a streaming iterator of bytes (default chunk 1 MiB).
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """
        Permanently deletes file at the target path.
        Returns True if deleted or already absent, False or raises StorageError if failed.
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Checks if file exists at target path.
        """
        pass

    @abstractmethod
    def stat(self, path: str) -> Dict[str, Any]:
        """
        Returns metadata about the file (size, length, modificationTime, replication, blockSize).
        """
        pass

    @abstractmethod
    def list_dir(self, path: str) -> list:
        """
        Lists directory contents.
        """
        pass

    @abstractmethod
    def cluster_info(self) -> Dict[str, Any]:
        """
        Returns cluster-wide storage metrics (total capacity, used, free, datanodes count).
        Admin only.
        """
        pass
