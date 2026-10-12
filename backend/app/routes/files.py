"""
File management routes for MiniCloud:
  - GET /api/files (search, filter, pagination, views: all, recent, starred, trash)
  - POST /api/files/upload (multipart/form-data upload with consistency protocol)
  - GET /api/files/<id>/download (streaming file download)
  - POST /api/files/<id>/download-token (short-lived signed URL download token)
  - PATCH /api/files/<id> (rename or move to folder)
  - POST /api/files/<id>/star & DELETE /api/files/<id>/star
  - DELETE /api/files/<id> (soft-delete to Trash)
  - POST /api/files/<id>/restore
  - DELETE /api/files/<id>/permanent
  - DELETE /api/trash (empty entire Trash)
"""
from flask import Blueprint, request, Response, stream_with_context, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from urllib.parse import quote

from app.database import get_db
from app.utils.response import api_success, api_error
from app.services.file_service import (
    execute_upload_consistency_protocol,
    execute_permanent_file_delete,
    generate_download_token,
    verify_download_token,
    sanitize_filename,
    get_file_category
)
from app.storage import get_storage_backend

files_bp = Blueprint("files", __name__, url_prefix="/api/files")

@files_bp.route("", methods=["GET"])
@jwt_required()
def list_files():
    user_id = int(get_jwt_identity())
    folder_id_param = request.args.get("folder_id")
    view = request.args.get("view", "all").lower()
    search_query = (request.args.get("q") or "").strip()
    sort_field = request.args.get("sort", "uploaded_at").lower()
    order = request.args.get("order", "desc").lower()
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 50))))
    offset = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor()

    conditions = ["user_id = ?"]
    params = [user_id]

    if view == "trash":
        conditions.append("is_deleted = 1")
    else:
        conditions.append("is_deleted = 0")
        if view == "starred":
            conditions.append("is_starred = 1")
        elif view == "recent":
            pass # Recent views show across all folders
        elif folder_id_param is not None and folder_id_param != "":
            conditions.append("folder_id = ?")
            params.append(int(folder_id_param))
        else:
            # Default root folder view
            conditions.append("folder_id IS NULL")

    if search_query:
        conditions.append("original_name LIKE ?")
        params.append(f"%{search_query}%")

    allowed_sort_fields = {
        "name": "original_name",
        "size": "file_size",
        "type": "extension",
        "uploaded_at": "uploaded_at",
        "last_accessed": "last_accessed_at"
    }
    sort_col = allowed_sort_fields.get(sort_field, "uploaded_at")
    sort_direction = "ASC" if order == "asc" else "DESC"

    where_clause = " AND ".join(conditions)

    # Count total
    cursor.execute(f"SELECT COUNT(*) AS total FROM files WHERE {where_clause};", params)
    total_count = cursor.fetchone()["total"]

    # Fetch rows
    fetch_query = f"""
    SELECT id, folder_id, original_name, stored_name, file_size, mime_type, extension,
           status, is_starred, is_deleted, uploaded_at, updated_at, last_accessed_at
    FROM files
    WHERE {where_clause}
    ORDER BY {sort_col} {sort_direction}
    LIMIT ? OFFSET ?;
    """
    params.extend([per_page, offset])
    cursor.execute(fetch_query, params)
    rows = cursor.fetchall()

    files_list = []
    for r in rows:
        item = dict(r)
        item["category"] = get_file_category(item.get("extension"))
        files_list.append(item)

    return api_success({
        "files": files_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "totalPages": (total_count + per_page - 1) // per_page
        }
    })

@files_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    user_id = int(get_jwt_identity())
    if "file" not in request.files:
        return api_error("NO_FILE_PROVIDED", "Multipart request must contain 'file'.")

    uploaded = request.files["file"]
    if not uploaded.filename:
        return api_error("EMPTY_FILENAME", "Uploaded file has no filename.")

    raw_folder_id = request.form.get("folder_id")
    folder_id = int(raw_folder_id) if raw_folder_id and raw_folder_id.isdigit() else None

    # Estimate size
    uploaded.seek(0, 2)
    file_size = uploaded.tell()
    uploaded.seek(0)

    if file_size > current_app.config["MAX_CONTENT_LENGTH"]:
        return api_error("FILE_TOO_LARGE", f"File exceeds maximum upload size of {current_app.config['MAX_UPLOAD_SIZE_MB']} MB.", status_code=413)

    try:
        saved_file = execute_upload_consistency_protocol(
            user_id=user_id,
            folder_id=folder_id,
            file_stream=uploaded.stream,
            original_name=uploaded.filename,
            file_size=file_size
        )
        saved_file["category"] = get_file_category(saved_file.get("extension"))
        return api_success(saved_file, status_code=201)
    except PermissionError as e:
        return api_error("QUOTA_EXCEEDED", str(e), status_code=413)
    except ValueError as e:
        return api_error("VALIDATION_ERROR", str(e), status_code=400)
    except Exception as e:
        current_app.logger.error("Upload error: %s", str(e))
        return api_error("UPLOAD_FAILED", f"File upload failed: {str(e)}", status_code=500)

@files_bp.route("/<int:file_id>/download-token", methods=["POST"])
@jwt_required()
def get_download_token(file_id: int):
    user_id = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM files WHERE id = ? AND user_id = ? AND is_deleted = 0;", (file_id, user_id))
    if not cursor.fetchone():
        return api_error("FILE_NOT_FOUND", "File not found.", status_code=404)

    token = generate_download_token(user_id, file_id)
    return api_success({"downloadToken": token, "expiresInSeconds": 60})

@files_bp.route("/<int:file_id>/download", methods=["GET"])
def download_file(file_id: int):
    # Authenticate via Header or signed query token
    auth_header = request.headers.get("Authorization", "")
    token_param = request.args.get("token")
    user_id = None

    if token_param:
        user_id = verify_download_token(token_param, file_id)
    elif auth_header.startswith("Bearer "):
        raw_jwt = auth_header[7:].strip()
        try:
            from flask_jwt_extended import decode_token
            decoded = decode_token(raw_jwt)
            user_id = int(decoded.get("sub"))
        except Exception as e:
            current_app.logger.warning("Download token decode error: %s", str(e))
            user_id = None

    if not user_id:
        return api_error("UNAUTHORIZED", "Valid authentication or download token required.", status_code=401)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id = ? AND user_id = ? AND is_deleted = 0;", (file_id, user_id))
    file_record = cursor.fetchone()

    if not file_record:
        return api_error("FILE_NOT_FOUND", "File not found.", status_code=404)

    # Update last_accessed_at
    with conn:
        conn.execute("UPDATE files SET last_accessed_at = CURRENT_TIMESTAMP WHERE id = ?;", (file_id,))

    storage = get_storage_backend(
        backend_type=current_app.config["STORAGE_BACKEND"],
        namenode_host=current_app.config["HDFS_NAMENODE_HOST"],
        webhdfs_port=current_app.config["HDFS_WEBHDFS_PORT"],
        base_path=current_app.config["HDFS_BASE_PATH"],
        hdfs_user=current_app.config["HDFS_USER"],
        mock_dir=current_app.config["MOCK_STORAGE_DIR"]
    )

    try:
        stream_iter = storage.download(file_record["hdfs_path"])
    except Exception as e:
        current_app.logger.error("Download stream failed: %s", str(e))
        return api_error("DOWNLOAD_FAILED", "Could not stream file from storage.", status_code=500)

    # RFC 5987 encoded Content-Disposition
    ascii_name = file_record["original_name"].encode("ascii", "replace").decode("ascii")
    utf8_encoded = quote(file_record["original_name"])
    content_disposition = f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_encoded}'

    response = Response(stream_with_context(stream_iter), mimetype=file_record["mime_type"])
    response.headers["Content-Disposition"] = content_disposition
    response.headers["Content-Length"] = str(file_record["file_size"])
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@files_bp.route("/<int:file_id>", methods=["PATCH"])
@jwt_required()
def update_file(file_id: int):
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    new_name = data.get("name")
    new_folder_id = data.get("folder_id")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id = ? AND user_id = ? AND is_deleted = 0;", (file_id, user_id))
    file_record = cursor.fetchone()

    if not file_record:
        return api_error("FILE_NOT_FOUND", "File not found.", status_code=404)

    updates = []
    params = []

    if new_name:
        clean = sanitize_filename(new_name)
        updates.append("original_name = ?")
        params.append(clean)

    if "folder_id" in data:
        target_folder = None if new_folder_id is None else int(new_folder_id)
        if target_folder is not None:
            cursor.execute("SELECT id FROM folders WHERE id = ? AND user_id = ? AND is_deleted = 0;", (target_folder, user_id))
            if not cursor.fetchone():
                return api_error("FOLDER_NOT_FOUND", "Destination folder does not exist.", status_code=404)
        updates.append("folder_id = ?")
        params.append(target_folder)

    if not updates:
        return api_error("NO_UPDATES", "No valid updates specified.")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([file_id, user_id])

    with conn:
        conn.execute(f"UPDATE files SET {', '.join(updates)} WHERE id = ? AND user_id = ?;", params)

    cursor.execute("SELECT * FROM files WHERE id = ?;", (file_id,))
    return api_success(dict(cursor.fetchone()))

@files_bp.route("/<int:file_id>/star", methods=["POST", "DELETE"])
@jwt_required()
def toggle_star(file_id: int):
    user_id = int(get_jwt_identity())
    is_starred = 1 if request.method == "POST" else 0

    conn = get_db()
    with conn:
        res = conn.execute(
            "UPDATE files SET is_starred = ? WHERE id = ? AND user_id = ? AND is_deleted = 0;",
            (is_starred, file_id, user_id)
        )
        if res.rowcount == 0:
            return api_error("FILE_NOT_FOUND", "File not found.", status_code=404)

    return api_success({"fileId": file_id, "isStarred": bool(is_starred)})

@files_bp.route("/<int:file_id>", methods=["DELETE"])
@jwt_required()
def soft_delete_file(file_id: int):
    user_id = int(get_jwt_identity())
    conn = get_db()
    with conn:
        res = conn.execute(
            "UPDATE files SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ? AND is_deleted = 0;",
            (file_id, user_id)
        )
        if res.rowcount == 0:
            return api_error("FILE_NOT_FOUND", "File not found.", status_code=404)

    return api_success({"message": "File moved to Trash."})

@files_bp.route("/<int:file_id>/restore", methods=["POST"])
@jwt_required()
def restore_file(file_id: int):
    user_id = int(get_jwt_identity())
    conn = get_db()
    with conn:
        res = conn.execute(
            "UPDATE files SET is_deleted = 0, deleted_at = NULL WHERE id = ? AND user_id = ? AND is_deleted = 1;",
            (file_id, user_id)
        )
        if res.rowcount == 0:
            return api_error("FILE_NOT_FOUND", "File not found in Trash.", status_code=404)

    return api_success({"message": "File restored from Trash."})

@files_bp.route("/<int:file_id>/permanent", methods=["DELETE"])
@jwt_required()
def permanent_delete_file(file_id: int):
    user_id = int(get_jwt_identity())
    try:
        deleted = execute_permanent_file_delete(user_id, file_id)
        if not deleted:
            return api_error("FILE_NOT_FOUND", "File not found.", status_code=404)
        return api_success({"message": "File permanently removed."})
    except Exception as e:
        return api_error("DELETE_FAILED", f"Permanent deletion failed: {str(e)}", status_code=500)

@files_bp.route("/trash", methods=["DELETE"])
@jwt_required()
def empty_trash():
    user_id = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM files WHERE user_id = ? AND is_deleted = 1;", (user_id,))
    trash_files = cursor.fetchall()

    deleted_count = 0
    for r in trash_files:
        try:
            execute_permanent_file_delete(user_id, r["id"])
            deleted_count += 1
        except Exception as e:
            current_app.logger.warning("Error deleting trash file %d: %s", r["id"], str(e))

    # Also clean up deleted folders permanently
    with conn:
        conn.execute("DELETE FROM folders WHERE user_id = ? AND is_deleted = 1;", (user_id,))

    return api_success({"message": f"Emptied trash: {deleted_count} files permanently removed."})
