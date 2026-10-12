"""
MiniCloud Metadata & Storage Reconciliation Script
Checks consistency between SQLite DB and physical HDFS / Mock storage:
  (a) Database records that have NO matching storage object (Ghost records).
  (b) Storage objects that have NO matching database record (Orphan files).

Usage:
  python scripts/reconcile.py              # Report only (safe)
  python scripts/reconcile.py --fix        # Interactive fix to purge ghosts and orphans
"""
import sys
import os
import argparse

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from app.config import Config
from app.database import get_db, init_db
from app.storage import get_storage_backend

def reconcile(fix_mode: bool = False):
    print("=" * 60)
    print(" MiniCloud Metadata vs Storage Reconciliation Utility")
    print(f" Active Storage Backend: [{Config.STORAGE_BACKEND.upper()}]")
    print("=" * 60)

    db_path = Config.DATABASE_PATH
    init_db(db_path)
    conn = get_db(db_path)
    cursor = conn.cursor()

    storage = get_storage_backend(
        backend_type=Config.STORAGE_BACKEND,
        namenode_host=Config.HDFS_NAMENODE_HOST,
        webhdfs_port=Config.HDFS_WEBHDFS_PORT,
        base_path=Config.HDFS_BASE_PATH,
        hdfs_user=Config.HDFS_USER,
        mock_dir=Config.MOCK_STORAGE_DIR
    )

    # 1. Check all DB files against storage
    cursor.execute("SELECT id, user_id, original_name, stored_name, hdfs_path, status FROM files;")
    db_files = cursor.fetchall()

    ghost_records = []
    registered_paths = set()

    for f in db_files:
        registered_paths.add(f["hdfs_path"])
        exists_in_storage = storage.exists(f["hdfs_path"])
        if not exists_in_storage:
            ghost_records.append(dict(f))

    print(f"\n1. Database File Records Scanned: {len(db_files)}")
    print(f"   Missing from storage (Ghost DB records): {len(ghost_records)}")
    for g in ghost_records:
        print(f"    - ID {g['id']} | User {g['user_id']} | '{g['original_name']}' | Path: {g['hdfs_path']}")

    # 2. Check storage files for user directories
    cursor.execute("SELECT id FROM users;")
    users = cursor.fetchall()
    orphan_files = []

    for u in users:
        u_dir = f"users/{u['id']}/files"
        try:
            items = storage.list_dir(u_dir)
            for item in items:
                filename = item.get("pathSuffix")
                if not filename:
                    continue
                full_rel_path = f"{u_dir}/{filename}"
                if full_rel_path not in registered_paths:
                    orphan_files.append({"path": full_rel_path, "size": item.get("length", 0)})
        except Exception:
            pass

    print(f"\n2. Storage Objects Scanned across {len(users)} users")
    print(f"   Unregistered Storage Files (Orphans): {len(orphan_files)}")
    for o in orphan_files:
        print(f"    - Orphan: {o['path']} ({o['size']} bytes)")

    # 3. Fix if requested
    if fix_mode:
        print("\n" + "=" * 60)
        confirm = input("Fix mode requested. Proceed to delete orphans and clean ghost DB rows? (yes/no): ")
        if confirm.strip().lower() == "yes":
            # Clean ghost records
            if ghost_records:
                with conn:
                    for g in ghost_records:
                        conn.execute("DELETE FROM files WHERE id = ?;", (g["id"],))
                print(f"[FIXED] Removed {len(ghost_records)} ghost records from database.")

            # Clean orphan storage objects
            if orphan_files:
                deleted_orphans = 0
                for o in orphan_files:
                    try:
                        storage.delete(o["path"])
                        deleted_orphans += 1
                    except Exception as e:
                        print(f"Failed to delete orphan {o['path']}: {e}")
                print(f"[FIXED] Removed {deleted_orphans} orphaned storage files.")
        else:
            print("Aborted fix mode.")

    print("\n" + "=" * 60)
    print(" Reconciliation scan completed.")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconcile MiniCloud metadata and storage")
    parser.add_argument("--fix", action="store_true", help="Clean up ghost records and orphaned files")
    args = parser.parse_args()
    reconcile(args.fix)
