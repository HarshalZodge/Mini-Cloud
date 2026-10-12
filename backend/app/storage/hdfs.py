"""
HdfsStorage implementation using WebHDFS REST API.
Handles:
  1. Two-step PUT upload handshake (307 redirect to DataNode).
  2. Streaming download via OPEN (op=OPEN).
  3. MKDIRS, DELETE, GETFILESTATUS.
  4. NameNode JMX metrics for cluster monitoring.
"""
import logging
import requests
from typing import Iterator, Dict, Any, Optional
from urllib.parse import urljoin, quote

from app.storage.base import (
    StorageBackend,
    StorageError,
    StorageUnavailableError,
    StorageNotFoundError
)

logger = logging.getLogger("minicloud.storage.hdfs")

class HdfsStorage(StorageBackend):
    def __init__(
        self,
        namenode_host: str = "localhost",
        webhdfs_port: int = 9870,
        base_path: str = "/minicloud",
        hdfs_user: str = "hadoop",
        replication_factor: int = 1,
        default_block_size: int = 134217728, # 128 MB
        timeout_seconds: int = 30
    ):
        self.namenode_host = namenode_host
        self.webhdfs_port = webhdfs_port
        self.base_path = base_path.rstrip('/')
        self.hdfs_user = hdfs_user
        self.replication_factor = replication_factor
        self.default_block_size = default_block_size
        self.timeout = timeout_seconds
        self.base_url = f"http://{self.namenode_host}:{self.webhdfs_port}"

    def _format_path(self, path: str) -> str:
        """Sanitizes and prefixes HDFS path."""
        p = path.strip()
        if not p.startswith('/'):
            p = f"{self.base_path}/{p}"
        return quote(p, safe="/-_.~")

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Internal requests wrapper with connection error handling and retry."""
        kwargs.setdefault('timeout', self.timeout)
        try:
            resp = requests.request(method, url, **kwargs)
            return resp
        except (requests.ConnectionError, requests.Timeout) as exc:
            logger.error("WebHDFS connection error on %s %s: %s", method, url, str(exc))
            raise StorageUnavailableError(
                f"Unable to reach HDFS NameNode at {self.namenode_host}:{self.webhdfs_port}",
                details={"url": url, "error": str(exc)}
            ) from exc

    def health(self) -> Dict[str, Any]:
        """Checks if NameNode WebHDFS is reachable and base directory is valid."""
        url = f"{self.base_url}/webhdfs/v1/?op=GETFILESTATUS&user.name={self.hdfs_user}"
        try:
            resp = self._request("GET", url)
            if resp.status_code == 200:
                return {
                    "healthy": True,
                    "backend": "hdfs",
                    "namenode": f"{self.namenode_host}:{self.webhdfs_port}",
                    "base_path": self.base_path
                }
            return {
                "healthy": False,
                "backend": "hdfs",
                "error": f"HTTP {resp.status_code}: {resp.text}"
            }
        except Exception as e:
            return {
                "healthy": False,
                "backend": "hdfs",
                "error": str(e)
            }

    def ensure_dir(self, path: str) -> bool:
        """Performs MKDIRS operation via WebHDFS."""
        formatted_path = self._format_path(path)
        url = f"{self.base_url}/webhdfs/v1{formatted_path}?op=MKDIRS&permission=755&user.name={self.hdfs_user}"
        resp = self._request("PUT", url)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("boolean", True)
        raise StorageError(f"Failed to ensure directory '{path}': {resp.text}", status_code=resp.status_code)

    def upload(self, path: str, stream: Any, size: int) -> Dict[str, Any]:
        """
        Executes the two-step WebHDFS upload protocol:
          Step 1: PUT to NameNode with allow_redirects=False -> 307 Temporary Redirect with DataNode Location
          Step 2: PUT file byte stream to the Location header URL
        """
        formatted_path = self._format_path(path)
        create_url = (
            f"{self.base_url}/webhdfs/v1{formatted_path}"
            f"?op=CREATE&overwrite=true"
            f"&replication={self.replication_factor}"
            f"&blocksize={self.default_block_size}"
            f"&user.name={self.hdfs_user}"
        )

        logger.debug("WebHDFS Step 1: Requesting upload URL from NameNode: %s", create_url)
        resp1 = self._request("PUT", create_url, allow_redirects=False)

        if resp1.status_code not in (307, 201):
            raise StorageError(
                f"WebHDFS CREATE handshake failed with status {resp1.status_code}: {resp1.text}",
                status_code=resp1.status_code
            )

        datanode_location = resp1.headers.get("Location")
        if not datanode_location:
            raise StorageError("NameNode did not provide a DataNode redirect Location header")

        logger.debug("WebHDFS Step 2: Uploading %d bytes directly to DataNode: %s", size, datanode_location)
        try:
            # Send file data or stream to DataNode
            resp2 = requests.put(
                datanode_location,
                data=stream,
                headers={"Content-Length": str(size)},
                timeout=max(self.timeout, 120)
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            logger.error("DataNode upload failed: %s", str(exc))
            # Attempt best effort cleanup
            self.delete(path)
            raise StorageUnavailableError(
                "DataNode upload connection failed. Ensure DataNode hostname/IP is reachable from controller.",
                details={"datanode_url": datanode_location, "error": str(exc)}
            ) from exc

        if resp2.status_code not in (200, 201):
            # Best effort cleanup
            self.delete(path)
            raise StorageError(
                f"DataNode write failed with status {resp2.status_code}: {resp2.text}",
                status_code=resp2.status_code
            )

        # Verify uploaded length
        stat_info = self.stat(path)
        actual_length = stat_info.get("length", 0)
        if actual_length != size:
            self.delete(path)
            raise StorageError(
                f"Uploaded file size mismatch. Expected {size} bytes, HDFS reported {actual_length} bytes."
            )

        return {
            "path": path,
            "size": actual_length,
            "replication": stat_info.get("replication", self.replication_factor),
            "blockSize": stat_info.get("blockSize", self.default_block_size)
        }

    def download(self, path: str, chunk_size: int = 1048576) -> Iterator[bytes]:
        """
        Executes streaming download from WebHDFS (op=OPEN) with 1 MiB chunks.
        """
        formatted_path = self._format_path(path)
        open_url = f"{self.base_url}/webhdfs/v1{formatted_path}?op=OPEN&user.name={self.hdfs_user}"
        try:
            resp = requests.get(open_url, stream=True, allow_redirects=True, timeout=self.timeout)
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise StorageUnavailableError(f"Failed to stream file from HDFS: {str(exc)}") from exc

        if resp.status_code == 404:
            raise StorageNotFoundError(f"File '{path}' does not exist on HDFS")
        if resp.status_code != 200:
            raise StorageError(f"WebHDFS OPEN failed with code {resp.status_code}: {resp.text}", status_code=resp.status_code)

        def generate() -> Iterator[bytes]:
            try:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        yield chunk
            finally:
                resp.close()

        return generate()

    def delete(self, path: str) -> bool:
        """Deletes a file or directory recursively in HDFS."""
        formatted_path = self._format_path(path)
        url = f"{self.base_url}/webhdfs/v1{formatted_path}?op=DELETE&recursive=true&user.name={self.hdfs_user}"
        resp = self._request("DELETE", url)
        if resp.status_code == 404:
            return True # Already gone
        if resp.status_code == 200:
            return resp.json().get("boolean", True)
        raise StorageError(f"Failed to delete '{path}' on HDFS: {resp.text}", status_code=resp.status_code)

    def exists(self, path: str) -> bool:
        """Returns True if path exists on HDFS."""
        try:
            self.stat(path)
            return True
        except StorageNotFoundError:
            return False
        except StorageError:
            return False

    def stat(self, path: str) -> Dict[str, Any]:
        """Queries metadata for a file or directory via GETFILESTATUS."""
        formatted_path = self._format_path(path)
        url = f"{self.base_url}/webhdfs/v1{formatted_path}?op=GETFILESTATUS&user.name={self.hdfs_user}"
        resp = self._request("GET", url)
        if resp.status_code == 404:
            raise StorageNotFoundError(f"File '{path}' not found on HDFS")
        if resp.status_code == 200:
            return resp.json().get("FileStatus", {})
        raise StorageError(f"GETFILESTATUS failed with code {resp.status_code}: {resp.text}", status_code=resp.status_code)

    def list_dir(self, path: str) -> list:
        """Lists directory contents via LISTSTATUS."""
        formatted_path = self._format_path(path)
        url = f"{self.base_url}/webhdfs/v1{formatted_path}?op=LISTSTATUS&user.name={self.hdfs_user}"
        resp = self._request("GET", url)
        if resp.status_code == 404:
            return []
        if resp.status_code == 200:
            statuses = resp.json().get("FileStatuses", {}).get("FileStatus", [])
            return statuses
        raise StorageError(f"LISTSTATUS failed with code {resp.status_code}: {resp.text}", status_code=resp.status_code)

    def cluster_info(self) -> Dict[str, Any]:
        """
        Pulls cluster statistics directly from NameNode JMX endpoint:
        /jmx?qry=Hadoop:service=NameNode,name=FSNamesystemState
        """
        jmx_url = f"{self.base_url}/jmx?qry=Hadoop:service=NameNode,name=FSNamesystemState"
        try:
            resp = self._request("GET", jmx_url)
            if resp.status_code != 200:
                return {"available": False, "error": f"HTTP {resp.status_code}"}
            
            beans = resp.json().get("beans", [])
            if not beans:
                return {"available": False, "error": "No JMX beans returned"}
            
            state = beans[0]
            capacity = state.get("CapacityTotal", 0)
            used = state.get("CapacityUsed", 0)
            remaining = state.get("CapacityRemaining", 0)
            num_live_datanodes = state.get("NumLiveDataNodes", 0)
            num_dead_datanodes = state.get("NumDeadDataNodes", 0)
            blocks_total = state.get("BlocksTotal", 0)

            return {
                "available": True,
                "capacityTotalBytes": capacity,
                "capacityUsedBytes": used,
                "capacityRemainingBytes": remaining,
                "numLiveDataNodes": num_live_datanodes,
                "numDeadDataNodes": num_dead_datanodes,
                "blocksTotal": blocks_total,
                "configuredReplication": self.replication_factor
            }
        except Exception as e:
            logger.warning("Could not retrieve JMX cluster info: %s", str(e))
            return {"available": False, "error": str(e)}
