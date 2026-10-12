"""
MiniCloud Storage Smoke Test Script
Can be run against Real WebHDFS or MockStorage.

Usage:
  python scripts/hdfs_smoke_test.py --backend mock
  python scripts/hdfs_smoke_test.py --backend hdfs --namenode 192.168.1.100 --port 9870 --user hadoop
"""
import sys
import os
import argparse
import hashlib
import io
import time

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from app.storage.hdfs import HdfsStorage
from app.storage.mock import MockStorage
from app.storage.base import StorageError, StorageUnavailableError

def run_smoke_test(storage, backend_name):
    print("=" * 60)
    print(f" MiniCloud Storage Smoke Test - Target: [{backend_name.upper()}]")
    print("=" * 60)

    # 1. Health Check
    print("\n1. Testing Backend Health...")
    health = storage.health()
    print(f"   -> Result: {health}")
    if not health.get("healthy"):
        print(f"   [FAIL] Backend is unhealthy: {health.get('error')}")
        return False
    print("   [PASS] Storage backend is healthy.")

    # 2. Directory Creation (ensure_dir)
    test_dir = "smoke_test_dir"
    print(f"\n2. Testing ensure_dir('{test_dir}')...")
    storage.ensure_dir(test_dir)
    print(f"   [PASS] Created directory: {test_dir}")

    # 3. File Upload with Checksum
    test_filename = f"{test_dir}/test_payload_{int(time.time())}.txt"
    payload = b"MiniCloud HDFS smoke test payload: Distributed Cloud SaaS File Storage Verification!"
    payload_size = len(payload)
    original_sha256 = hashlib.sha256(payload).hexdigest()
    print(f"\n3. Testing upload to '{test_filename}' ({payload_size} bytes)...")
    print(f"   Original SHA-256: {original_sha256}")

    upload_result = storage.upload(test_filename, io.BytesIO(payload), payload_size)
    print(f"   -> Upload Result: {upload_result}")
    print("   [PASS] File uploaded.")

    # 4. Stat & Exists Check
    print(f"\n4. Testing exists() and stat()...")
    if not storage.exists(test_filename):
        print(f"   [FAIL] exists('{test_filename}') returned False!")
        return False
    
    stat_info = storage.stat(test_filename)
    reported_length = stat_info.get("length", 0)
    print(f"   -> Stat Info: length={reported_length}, replication={stat_info.get('replication')}")
    if reported_length != payload_size:
        print(f"   [FAIL] Length mismatch! Expected {payload_size}, got {reported_length}")
        return False
    print("   [PASS] Stat and length verified.")

    # 5. Download & SHA-256 Verification
    print(f"\n5. Testing streaming download and SHA-256 verification...")
    downloaded_bytes = b"".join(list(storage.download(test_filename)))
    downloaded_sha256 = hashlib.sha256(downloaded_bytes).hexdigest()
    print(f"   Downloaded size: {len(downloaded_bytes)} bytes")
    print(f"   Downloaded SHA-256: {downloaded_sha256}")

    if downloaded_sha256 != original_sha256:
        print("   [FAIL] Integrity checksum failure! Hashes do not match!")
        return False
    print("   [PASS] Exact byte match verified!")

    # 6. Cluster Info
    print(f"\n6. Testing cluster_info()...")
    cluster = storage.cluster_info()
    print(f"   -> Cluster info: {cluster}")
    print("   [PASS] Cluster metrics returned.")

    # 7. Cleanup (delete)
    print(f"\n7. Testing deletion of '{test_filename}' and directory...")
    storage.delete(test_filename)
    if storage.exists(test_filename):
        print("   [FAIL] File still exists after deletion!")
        return False
    storage.delete(test_dir)
    print("   [PASS] File and test directory cleaned up successfully.")

    print("\n" + "=" * 60)
    print(f" ALL SMOKE TEST STEPS PASSED FOR [{backend_name.upper()}]!")
    print("=" * 60)
    return True

def main():
    parser = argparse.ArgumentParser(description="MiniCloud Storage Smoke Test")
    parser.add_argument("--backend", choices=["hdfs", "mock"], default="mock", help="Storage backend to test")
    parser.add_argument("--namenode", default="localhost", help="HDFS NameNode hostname/IP")
    parser.add_argument("--port", type=int, default=9870, help="WebHDFS port (default: 9870)")
    parser.add_argument("--base-path", default="/minicloud", help="HDFS root path")
    parser.add_argument("--user", default="hadoop", help="HDFS user for WebHDFS operations")
    args = parser.parse_args()

    if args.backend == "hdfs":
        storage = HdfsStorage(
            namenode_host=args.namenode,
            webhdfs_port=args.port,
            base_path=args.base_path,
            hdfs_user=args.user
        )
    else:
        storage = MockStorage(base_dir="./mock_storage")

    try:
        success = run_smoke_test(storage, args.backend)
        sys.exit(0 if success else 1)
    except StorageUnavailableError as e:
        print(f"\n[ERROR] Storage engine unavailable: {e.message}")
        if e.details:
            print(f"Details: {e.details}")
        sys.exit(2)
    except StorageError as e:
        print(f"\n[ERROR] Storage error: {e.message}")
        sys.exit(3)
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(4)

if __name__ == "__main__":
    main()
