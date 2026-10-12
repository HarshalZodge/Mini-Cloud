# MiniCloud REST API Documentation

Base URL: `http://<SERVER_HOST>:5000`

All responses follow a standard envelope:
- **Success**: `{ "success": true, "data": { ... } }`
- **Error**: `{ "success": false, "error": { "code": "STRING_CODE", "message": "Human readable message", "details": ... } }`

---

## 1. Authentication (`/api/auth`)

### `POST /api/auth/register`
Creates a user account. The first registered user is automatically given role `admin`; all subsequent users are `user`.
- **Request Body**:
  ```json
  { "username": "student", "email": "student@minicloud.lan", "password": "Password123" }
  ```
- **Response** (201 Created):
  ```json
  {
    "success": true,
    "data": {
      "token": "eyJhbGciOi...",
      "user": { "id": 1, "username": "student", "email": "student@minicloud.lan", "role": "admin", "storageQuotaMb": 1024 }
    }
  }
  ```

### `POST /api/auth/login`
Authenticates a user with username or email.
- **Request Body**: `{ "identifier": "student", "password": "Password123" }`
- **Response** (200 OK): Contains JWT token and user info.

### `POST /api/auth/logout`
Revokes the current JWT token by adding its `jti` to `token_blocklist`.
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200 OK): `{ "success": true, "data": { "message": "Successfully logged out." } }`

### `GET /api/auth/me`
Retrieves currently logged-in user profile, role, and storage usage.
- **Headers**: `Authorization: Bearer <token>`

---

## 2. File Operations (`/api/files`)

### `GET /api/files`
Query parameters:
- `folder_id` (optional): Parent folder ID. Omit for root.
- `view` (optional): `all`, `recent`, `starred`, `trash`.
- `q` (optional): Filename search query.
- `sort`: `name`, `size`, `type`, `uploaded_at`, `last_accessed`.
- `order`: `asc` or `desc`.
- `page`, `per_page`: Pagination (default 50).

### `POST /api/files/upload`
Uploads a file using multipart/form-data. Executes the 6-step consistency protocol.
- **Headers**: `Authorization: Bearer <token>`
- **Body**: `file` (binary), `folder_id` (optional).
- **Response** (201 Created): File metadata.
- **Errors**: `413 QUOTA_EXCEEDED`, `413 PAYLOAD_TOO_LARGE`, `400 VALIDATION_ERROR`.

### `GET /api/files/{id}/download`
Streams file content with `Content-Disposition` header.
- **Auth**: Supported via `Authorization: Bearer <token>` header OR `?token=<signed_token>`.

### `POST /api/files/{id}/download-token`
Generates a 60-second single-use signed download token for browser link downloads.
- **Response** (200 OK): `{ "downloadToken": "...", "expiresInSeconds": 60 }`

### `PATCH /api/files/{id}`
Rename a file or move it to another folder.
- **Body**: `{ "name": "new_name.txt", "folder_id": 2 }`

### `POST /api/files/{id}/star` / `DELETE /api/files/{id}/star`
Toggle starred status.

### `DELETE /api/files/{id}`
Soft-deletes file to Trash.

### `POST /api/files/{id}/restore`
Restores file from Trash.

### `DELETE /api/files/{id}/permanent`
Permanently deletes physical file from HDFS first, then deletes database record.

### `DELETE /api/trash`
Empties entire Trash for the authenticated user.

---

## 3. Folder Operations (`/api/folders`)

### `GET /api/folders`
Lists virtual subfolders for a parent folder.

### `POST /api/folders`
Creates a new virtual folder. Unique name per level enforced.
- **Body**: `{ "name": "Assignments", "parent_folder_id": null }`

### `GET /api/folders/{id}/contents`
Retrieves folder breadcrumb path, subfolders, and files.

### `PATCH /api/folders/{id}`
Renames folder.

### `DELETE /api/folders/{id}`
Soft-deletes folder and all its contents to Trash.

### `POST /api/folders/{id}/restore`
Restores folder and its contents.

---

## 4. Analytics & Cluster (`/api/dashboard`, `/api/storage`, `/api/admin/cluster`)

### `GET /api/dashboard/stats`
Returns total file count, folder count, used bytes, quota bytes, and file-type donut distribution.

### `GET /api/dashboard/recent-files`
Returns up to 10 recently accessed or uploaded files.

### `GET /api/storage/usage`
Returns user quota vs cluster storage capacity and detailed category byte breakdowns.

### `GET /api/admin/cluster`
(Admin only) Returns live/dead DataNodes, HDFS raw capacity, block count, and configured replication factor from NameNode JMX.
