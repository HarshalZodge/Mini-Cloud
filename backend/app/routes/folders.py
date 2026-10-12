"""
Virtual folder routes for MiniCloud:
  - GET /api/folders (list folders for current parent)
  - POST /api/folders (create folder)
  - GET /api/folders/<id>/contents (retrieve breadcrumbs and child items)
  - PATCH /api/folders/<id> (rename folder)
  - DELETE /api/folders/<id> (move folder to Trash)
  - POST /api/folders/<id>/restore (restore folder from Trash)
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.utils.response import api_success, api_error
from app.services.folder_service import (
    create_folder,
    get_folder_hierarchy_path,
    soft_delete_folder,
    restore_folder
)

folders_bp = Blueprint("folders", __name__, url_prefix="/api/folders")

@folders_bp.route("", methods=["GET"])
@jwt_required()
def list_folders():
    user_id = int(get_jwt_identity())
    parent_id_param = request.args.get("parent_id")
    parent_id = int(parent_id_param) if parent_id_param and parent_id_param.isdigit() else None

    conn = get_db()
    cursor = conn.cursor()

    if parent_id is not None:
        cursor.execute(
            """
            SELECT id, parent_folder_id, folder_name, created_at, updated_at
            FROM folders 
            WHERE user_id = ? AND parent_folder_id = ? AND is_deleted = 0
            ORDER BY folder_name ASC;
            """,
            (user_id, parent_id)
        )
    else:
        cursor.execute(
            """
            SELECT id, parent_folder_id, folder_name, created_at, updated_at
            FROM folders 
            WHERE user_id = ? AND parent_folder_id IS NULL AND is_deleted = 0
            ORDER BY folder_name ASC;
            """,
            (user_id,)
        )

    rows = [dict(r) for r in cursor.fetchall()]
    breadcrumbs = get_folder_hierarchy_path(conn, parent_id, user_id)

    return api_success({
        "folders": rows,
        "breadcrumbs": breadcrumbs
    })

@folders_bp.route("", methods=["POST"])
@jwt_required()
def create_new_folder():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    name = data.get("name") or ""
    parent_id = data.get("parent_folder_id")

    try:
        new_folder = create_folder(user_id, name, parent_id)
        return api_success(new_folder, status_code=201)
    except FileExistsError as e:
        return api_error("FOLDER_EXISTS", str(e), status_code=409)
    except ValueError as e:
        return api_error("INVALID_INPUT", str(e), status_code=400)

@folders_bp.route("/<int:folder_id>/contents", methods=["GET"])
@jwt_required()
def get_folder_contents(folder_id: int):
    user_id = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor()

    # Check folder ownership
    cursor.execute("SELECT * FROM folders WHERE id = ? AND user_id = ? AND is_deleted = 0;", (folder_id, user_id))
    folder = cursor.fetchone()
    if not folder:
        return api_error("FOLDER_NOT_FOUND", "Folder not found.", status_code=404)

    # Subfolders
    cursor.execute(
        "SELECT id, parent_folder_id, folder_name, created_at FROM folders WHERE user_id = ? AND parent_folder_id = ? AND is_deleted = 0 ORDER BY folder_name ASC;",
        (user_id, folder_id)
    )
    subfolders = [dict(r) for r in cursor.fetchall()]

    # Contained Files
    cursor.execute(
        "SELECT id, folder_id, original_name, file_size, mime_type, extension, is_starred, uploaded_at, last_accessed_at FROM files WHERE user_id = ? AND folder_id = ? AND is_deleted = 0 ORDER BY original_name ASC;",
        (user_id, folder_id)
    )
    files = [dict(r) for r in cursor.fetchall()]

    breadcrumbs = get_folder_hierarchy_path(conn, folder_id, user_id)

    return api_success({
        "currentFolder": dict(folder),
        "breadcrumbs": breadcrumbs,
        "folders": subfolders,
        "files": files
    })

@folders_bp.route("/<int:folder_id>", methods=["PATCH"])
@jwt_required()
def update_folder(folder_id: int):
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()

    if not new_name:
        return api_error("INVALID_NAME", "Folder name cannot be empty.")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM folders WHERE id = ? AND user_id = ? AND is_deleted = 0;", (folder_id, user_id))
    folder = cursor.fetchone()
    if not folder:
        return api_error("FOLDER_NOT_FOUND", "Folder not found.", status_code=404)

    # Check for name collision in same parent
    cursor.execute(
        "SELECT id FROM folders WHERE user_id = ? AND IFNULL(parent_folder_id, -1) = IFNULL(?, -1) AND folder_name = ? COLLATE NOCASE AND id != ? AND is_deleted = 0;",
        (user_id, folder["parent_folder_id"], new_name, folder_id)
    )
    if cursor.fetchone():
        return api_error("FOLDER_EXISTS", f"A folder named '{new_name}' already exists in this directory.", status_code=409)

    with conn:
        conn.execute("UPDATE folders SET folder_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (new_name, folder_id))

    cursor.execute("SELECT * FROM folders WHERE id = ?;", (folder_id,))
    return api_success(dict(cursor.fetchone()))

@folders_bp.route("/<int:folder_id>", methods=["DELETE"])
@jwt_required()
def delete_folder(folder_id: int):
    user_id = int(get_jwt_identity())
    success = soft_delete_folder(user_id, folder_id)
    if not success:
        return api_error("FOLDER_NOT_FOUND", "Folder not found.", status_code=404)
    return api_success({"message": "Folder and contents moved to Trash."})

@folders_bp.route("/<int:folder_id>/restore", methods=["POST"])
@jwt_required()
def restore_deleted_folder(folder_id: int):
    user_id = int(get_jwt_identity())
    restore_folder(user_id, folder_id)
    return api_success({"message": "Folder restored."})
