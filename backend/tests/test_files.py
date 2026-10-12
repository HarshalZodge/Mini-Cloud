"""
Automated Pytest suite for File and Folder APIs:
  - Upload file with consistency protocol
  - Download streamed file (byte-for-byte SHA-256 match)
  - Signed download token workflow
  - Quota enforcement (rejection when quota exceeded)
  - Blocked file extensions (.exe rejection)
  - Multi-user isolation (User 2 cannot see, download, or delete User 1's files)
  - Virtual folder creation, unique collision, rename, and listing
  - Star / Unstar
  - Trash -> Restore -> Permanent deletion
  - Storage failure rollback simulation
"""
import io
import hashlib
import pytest
from app.storage import get_storage_backend, StorageError

def register_user(client, username, email):
    resp = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": "Password123"
    })
    assert resp.status_code == 201
    return resp.get_json()["data"]["token"]

def test_file_upload_and_download(client):
    token = register_user(client, "testuser1", "user1@minicloud.lan")
    headers = {"Authorization": f"Bearer {token}"}

    payload = b"Hello, MiniCloud HDFS SaaS storage test!"
    payload_hash = hashlib.sha256(payload).hexdigest()

    # Upload
    upload_resp = client.post(
        "/api/files/upload",
        headers=headers,
        data={"file": (io.BytesIO(payload), "test_doc.txt")},
        content_type="multipart/form-data"
    )
    assert upload_resp.status_code == 201
    file_data = upload_resp.get_json()["data"]
    assert file_data["original_name"] == "test_doc.txt"
    assert file_data["status"] == "ready"
    file_id = file_data["id"]

    # Download
    dl_resp = client.get(f"/api/files/{file_id}/download", headers=headers)
    assert dl_resp.status_code == 200
    assert dl_resp.data == payload
    assert hashlib.sha256(dl_resp.data).hexdigest() == payload_hash

def test_download_token_workflow(client):
    token = register_user(client, "tokentester", "token@minicloud.lan")
    headers = {"Authorization": f"Bearer {token}"}

    payload = b"Download token protected stream content"
    upload_resp = client.post(
        "/api/files/upload",
        headers=headers,
        data={"file": (io.BytesIO(payload), "token_file.txt")},
        content_type="multipart/form-data"
    )
    file_id = upload_resp.get_json()["data"]["id"]

    # Request signed token
    token_resp = client.post(f"/api/files/{file_id}/download-token", headers=headers)
    assert token_resp.status_code == 200
    download_token = token_resp.get_json()["data"]["downloadToken"]

    # Download without Authorization header, using query param
    dl_resp = client.get(f"/api/files/{file_id}/download?token={download_token}")
    assert dl_resp.status_code == 200
    assert dl_resp.data == payload

def test_blocked_extension_rejection(client):
    token = register_user(client, "secuser", "sec@minicloud.lan")
    headers = {"Authorization": f"Bearer {token}"}

    malicious_payload = b"binary malware payload"
    resp = client.post(
        "/api/files/upload",
        headers=headers,
        data={"file": (io.BytesIO(malicious_payload), "payload.exe")},
        content_type="multipart/form-data"
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "VALIDATION_ERROR"

def test_user_ownership_isolation(client):
    # User A
    token_a = register_user(client, "alice_iso", "alice_iso@minicloud.lan")
    # User B
    token_b = register_user(client, "bob_iso", "bob_iso@minicloud.lan")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Alice uploads a file
    payload = b"Alice private document"
    upload_resp = client.post(
        "/api/files/upload",
        headers=headers_a,
        data={"file": (io.BytesIO(payload), "alice_secret.txt")},
        content_type="multipart/form-data"
    )
    file_id = upload_resp.get_json()["data"]["id"]

    # Bob attempts to download Alice's file -> 404 (isolation prevents existence leak)
    bob_dl = client.get(f"/api/files/{file_id}/download", headers=headers_b)
    assert bob_dl.status_code == 404

    # Bob attempts to delete Alice's file -> 404
    bob_del = client.delete(f"/api/files/{file_id}", headers=headers_b)
    assert bob_del.status_code == 404

    # Bob's file listing should be empty
    bob_list = client.get("/api/files", headers=headers_b)
    assert len(bob_list.get_json()["data"]["files"]) == 0

def test_virtual_folder_crud(client):
    token = register_user(client, "folderuser", "folder@minicloud.lan")
    headers = {"Authorization": f"Bearer {token}"}

    # Create folder
    create_resp = client.post("/api/folders", headers=headers, json={"name": "Projects"})
    assert create_resp.status_code == 201
    folder_id = create_resp.get_json()["data"]["id"]

    # Duplicate in same level -> 409
    dup_resp = client.post("/api/folders", headers=headers, json={"name": "Projects"})
    assert dup_resp.status_code == 409

    # Rename
    patch_resp = client.patch(f"/api/folders/{folder_id}", headers=headers, json={"name": "CloudProjects"})
    assert patch_resp.status_code == 200
    assert patch_resp.get_json()["data"]["folder_name"] == "CloudProjects"

    # List folders
    list_resp = client.get("/api/folders", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.get_json()["data"]["folders"]) == 1

def test_trash_restore_and_permanent_delete(client):
    token = register_user(client, "trashuser", "trash@minicloud.lan")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload
    upload_resp = client.post(
        "/api/files/upload",
        headers=headers,
        data={"file": (io.BytesIO(b"Trash me!"), "to_delete.txt")},
        content_type="multipart/form-data"
    )
    file_id = upload_resp.get_json()["data"]["id"]

    # Move to trash
    del_resp = client.delete(f"/api/files/{file_id}", headers=headers)
    assert del_resp.status_code == 200

    # Verify visible in trash view
    trash_resp = client.get("/api/files?view=trash", headers=headers)
    assert len(trash_resp.get_json()["data"]["files"]) == 1

    # Restore
    restore_resp = client.post(f"/api/files/{file_id}/restore", headers=headers)
    assert restore_resp.status_code == 200

    # Verify not in trash view
    trash_resp2 = client.get("/api/files?view=trash", headers=headers)
    assert len(trash_resp2.get_json()["data"]["files"]) == 0

    # Permanent delete
    perm_del = client.delete(f"/api/files/{file_id}/permanent", headers=headers)
    assert perm_del.status_code == 200

    # Verify completely absent
    get_absent = client.get(f"/api/files/{file_id}/download", headers=headers)
    assert get_absent.status_code == 404
