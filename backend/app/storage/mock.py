"""
MockStorage implementation for local file system operations.
Used during automated testing and UI development without requiring an active HDFS cluster.
"""
import os
import shutil
import logging
from typing import Iterator, Dict, Any

from app.storage.base import (
    StorageBackend,
    StorageNotFoundError,
    StorageError
)

logger = logging.getLogger("minicloud.storage.mock")

class MockStorage(StorageBackend):
    def __init__(self, base_dir: str = "./mock_storage"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, path: str) -> str:
        clean = path.lstrip('/\\').replace('\\', '/')
        full_path = os.path.abspath(os.path.join(self.base_dir, clean))
        # Prevent directory traversal attacks
        if not full_path.startswith(self.base_dir):
            raise StorageError("Path traversal detected in mock storage")
        return full_path

    def health(self) -> Dict[str, Any]:
        return {
            "healthy": True,
            "backend": "mock",
            "base_dir": self.base_dir,
            "status": "Mock filesystem operational"
        }

    def ensure_dir(self, path: str) -> bool:
        full_path = self._resolve_path(path)
        os.makedirs(full_path, exist_ok=True)
        return True

    def upload(self, path: str, stream: Any, size: int) -> Dict[str, Any]:
        full_path = self._resolve_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        bytes_written = 0
        with open(full_path, "wb") as f:
            if hasattr(stream, "read"):
                while True:
                    chunk = stream.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_written += len(chunk)
            elif isinstance(stream, (bytes, bytearray)):
                f.write(stream)
                bytes_written = len(stream)
            else:
                for chunk in stream:
                    f.write(chunk)
                    bytes_written += len(chunk)

        return {
            "path": path,
            "size": bytes_written,
            "replication": 1,
            "blockSize": 134217728
        }

    def download(self, path: str, chunk_size: int = 1048576) -> Iterator[bytes]:
        full_path = self._resolve_path(path)
        if not os.path.exists(full_path):
            raise StorageNotFoundError(f"Mock file '{path}' not found")

        def generate() -> Iterator[bytes]:
            with open(full_path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        return generate()

    def delete(self, path: str) -> bool:
        full_path = self._resolve_path(path)
        if not os.path.exists(full_path):
            return True
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        return True

    def exists(self, path: str) -> bool:
        full_path = self._resolve_path(path)
        return os.path.exists(full_path)

    def stat(self, path: str) -> Dict[str, Any]:
        full_path = self._resolve_path(path)
        if not os.path.exists(full_path):
            raise StorageNotFoundError(f"Mock file '{path}' not found")

        stat_result = os.stat(full_path)
        return {
            "length": stat_result.st_size,
            "type": "DIRECTORY" if os.path.isdir(full_path) else "FILE",
            "modificationTime": int(stat_result.st_mtime * 1000),
            "replication": 1,
            "blockSize": 134217728
        }

    def list_dir(self, path: str) -> list:
        full_path = self._resolve_path(path)
        if not os.path.exists(full_path):
            return []
        items = []
        for name in os.listdir(full_path):
            item_path = os.path.join(full_path, name)
            st = os.stat(item_path)
            items.append({
                "pathSuffix": name,
                "type": "DIRECTORY" if os.path.isdir(item_path) else "FILE",
                "length": st.st_size
            })
        return items

    def cluster_info(self) -> Dict[str, Any]:
        total, used, free = shutil.disk_usage(self.base_dir)
        return {
            "available": True,
            "capacityTotalBytes": total,
            "capacityUsedBytes": used,
            "capacityRemainingBytes": free,
            "numLiveDataNodes": 1,
            "numDeadDataNodes": 0,
            "blocksTotal": 1,
            "configuredReplication": 1
        }
