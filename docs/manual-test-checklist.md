# MiniCloud Manual Test Checklist

Use this checklist to perform rigorous pre-submission verification in both Mock Storage and Real HDFS environments.

---

## 1. Environment & Setup Verification
- [ ] Run `powershell -ExecutionPolicy Bypass -File .\scripts\check-env.ps1`. Verify Python, Node.js, and npm are detected.
- [ ] Verify `backend/.env` exists and contains secret keys, storage configuration, and blocked extensions.
- [ ] If using real HDFS: Verify Hadoop daemons are running on Ubuntu VM (`jps` shows `NameNode`, `DataNode`, `SecondaryNameNode`).
- [ ] If using real HDFS: Verify WebHDFS root responds: `curl "http://<VM_IP>:9870/webhdfs/v1/?op=GETFILESTATUS&user.name=hadoop"`.

---

## 2. Storage Engine Standalone Tests
- [ ] Run mock smoke test: `python .\scripts\hdfs_smoke_test.py --backend mock`. (All 7 steps PASS).
- [ ] If using real HDFS: Run real smoke test: `python .\scripts\hdfs_smoke_test.py --backend hdfs --namenode <VM_IP> --port 9870`. (Verify exact SHA-256 match).
- [ ] Run test with incorrect IP/port: verify script fails cleanly with code 1 or 2 without falling back to local disk.

---

## 3. Automated Pytest Backend Test Suites
- [ ] Run `python -m pytest .\backend\tests\test_auth.py -v`. (All 6 tests PASS).
- [ ] Run `python -m pytest .\backend\tests\test_files.py -v`. (All 6 tests PASS).
- [ ] Run `python .\scripts\reconcile.py`. (Verify 0 ghosts and 0 orphans).

---

## 4. Frontend & Single-Port Verification
- [ ] Run `npm run build` in `frontend/`. (Verify bundle builds cleanly without error).
- [ ] Start production server: `python -m waitress --host=0.0.0.0 --port=5000 app:app` from `backend/`.
- [ ] Open `http://localhost:5000` in browser. Verify login page appears.
- [ ] Refresh browser on deep URLs (`http://localhost:5000/dashboard`, `http://localhost:5000/files`). Verify SPA catch-all serves page without 404.

---

## 5. End-to-End User Flow (Browser)
- [ ] **First Registration**: Register `admin_user`. Verify user role is `admin`.
- [ ] **Theme Switching**: Toggle dark mode icon in top bar. Verify theme persists upon page refresh.
- [ ] **Folder Creation**: Click **New Folder**, enter `ClassNotes`. Verify folder appears in list.
- [ ] **Duplicate Prevention**: Try creating another folder named `ClassNotes`. Verify HTTP 409 error toast appears.
- [ ] **File Upload**: Upload a 5 MB file into `ClassNotes`. Verify progress bar animates smoothly and completes.
- [ ] **Filename Collision**: Upload a file with the same name. Verify it auto-renames to `file (1).ext`.
- [ ] **Malware Block**: Try uploading a `.exe` or `.bat` file. Verify controller rejects it with a validation error.
- [ ] **Download**: Click download button. Verify downloaded file opens correctly and is not corrupted.
- [ ] **Move File**: Move a file into another folder. Verify it disappears from source and appears in destination.
- [ ] **Star File**: Star a file. Navigate to `/starred`. Verify file is listed.
- [ ] **Soft Delete**: Delete file. Verify it moves to `/trash` and is hidden from My Files.
- [ ] **Quota Accounting**: Verify storage used on Dashboard still counts trashed files until emptied.
- [ ] **Restore**: Restore file from Trash. Verify it returns to its original folder.
- [ ] **Empty Trash**: Empty trash. Verify physical file is purged from storage.

---

## 6. Multi-Tenant Isolation
- [ ] Open Incognito/Private window.
- [ ] Register `student_user`. Verify assigned role is `user`.
- [ ] Verify `student_user` sees an empty file list.
- [ ] Attempt to access `/cluster` URL as `student_user`. Verify redirected back to `/dashboard` (admin protected).
- [ ] Log out as `student_user`. Attempt to use old JWT token. Verify HTTP 401 `TOKEN_REVOKED` response.

---

## 7. LAN Demonstration Test
- [ ] Find host IP using `ipconfig` (e.g. `192.168.1.100`).
- [ ] Run firewall allow rule for port 5000 in Administrator PowerShell.
- [ ] Connect a phone or second laptop to the same Wi-Fi/LAN.
- [ ] Open `http://192.168.1.100:5000` on the mobile device.
- [ ] Log in and upload an image from the mobile device.
- [ ] Refresh host laptop: verify image uploaded by phone is immediately visible.
