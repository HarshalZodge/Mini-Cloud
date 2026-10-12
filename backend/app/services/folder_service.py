"""
Folder service managing virtual folder operations in SQLite.
Folders are purely virtual - no physical directories are created on HDFS.
"""
from typing import Optional, List, Dict, Any
from app.database import get_db

def create_folder(user_id: int, folder_name: str, parent_folder_id: Optional[int] = None) -> Dict[str, Any]:
    name = folder_name.strip()
    if not name:
        raise ValueError("Folder name cannot be empty.")
    if "/" in name or "\\" in name:
        raise ValueError("Folder name cannot contain path separators.")

    conn = get_db()
    cursor = conn.cursor()

    if parent_folder_id is not None:
        cursor.execute("SELECT id FROM folders WHERE id = ? AND user_id = ? AND is_deleted = 0;", (parent_folder_id, user_id))
        if not cursor.fetchone():
            raise ValueError("Parent folder does not exist.")

    # Check for duplicate
    cursor.execute(
        """
        SELECT id FROM folders 
        WHERE user_id = ? AND IFNULL(parent_folder_id, -1) = IFNULL(?, -1) 
          AND folder_name = ? COLLATE NOCASE AND is_deleted = 0;
        """,
        (user_id, parent_folder_id, name)
    )
    if cursor.fetchone():
        raise FileExistsError(f"A folder named '{name}' already exists in this directory.")

    with conn:
        cursor.execute(
            """
            INSERT INTO folders (user_id, parent_folder_id, folder_name)
            VALUES (?, ?, ?);
            """,
            (user_id, parent_folder_id, name)
        )
        folder_id = cursor.lastrowid

    cursor.execute("SELECT * FROM folders WHERE id = ?;", (folder_id,))
    return dict(cursor.fetchone())

def get_folder_hierarchy_path(conn, folder_id: Optional[int], user_id: int) -> List[Dict[str, Any]]:
    """Builds breadcrumb path list: [{id: 1, name: 'Documents'}, ...]"""
    if folder_id is None:
        return []

    breadcrumbs = []
    current_id = folder_id
    cursor = conn.cursor()

    while current_id is not None:
        cursor.execute("SELECT id, parent_folder_id, folder_name FROM folders WHERE id = ? AND user_id = ?;", (current_id, user_id))
        row = cursor.fetchone()
        if not row:
            break
        breadcrumbs.append({"id": row["id"], "name": row["folder_name"]})
        current_id = row["parent_folder_id"]

    breadcrumbs.reverse()
    return breadcrumbs

def soft_delete_folder(user_id: int, folder_id: int) -> bool:
    """Soft-deletes a folder and all its contents (moves them to Trash)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM folders WHERE id = ? AND user_id = ? AND is_deleted = 0;", (folder_id, user_id))
    if not cursor.fetchone():
        return False

    with conn:
        # Mark folder deleted
        conn.execute("UPDATE folders SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP WHERE id = ?;", (folder_id,))
        # Mark immediate files deleted
        conn.execute("UPDATE files SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP WHERE folder_id = ? AND user_id = ?;", (folder_id, user_id))

    return True

def restore_folder(user_id: int, folder_id: int) -> bool:
    """Restores a soft-deleted folder and its immediate files."""
    conn = get_db()
    with conn:
        conn.execute("UPDATE folders SET is_deleted = 0, deleted_at = NULL WHERE id = ? AND user_id = ?;", (folder_id, user_id))
        conn.execute("UPDATE files SET is_deleted = 0, deleted_at = NULL WHERE folder_id = ? AND user_id = ?;", (folder_id, user_id))
    return True
