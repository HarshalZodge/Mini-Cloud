"""
Dashboard, Storage Analytics, and Cluster status endpoints for MiniCloud:
  - GET /api/dashboard/stats
  - GET /api/dashboard/recent-files
  - GET /api/storage/usage
  - GET /api/admin/cluster (Admin only: live/dead DataNodes, HDFS raw metrics)
"""
from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.database import get_db
from app.utils.response import api_success, api_error
from app.storage import get_storage_backend
from app.services.file_service import get_file_category

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/api/dashboard/stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    user_id = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor()

    # User quota
    cursor.execute("SELECT storage_quota_mb FROM users WHERE id = ?;", (user_id,))
    user_row = cursor.fetchone()
    quota_mb = user_row["storage_quota_mb"] if user_row else 1024
    quota_bytes = quota_mb * 1024 * 1024

    # Ready files count and storage used
    cursor.execute(
        """
        SELECT 
            COUNT(id) AS total_files,
            IFNULL(SUM(file_size), 0) AS used_bytes
        FROM files 
        WHERE user_id = ? AND is_deleted = 0 AND status = 'ready';
        """,
        (user_id,)
    )
    file_stats = cursor.fetchone()
    total_files = file_stats["total_files"]
    used_bytes = file_stats["used_bytes"]

    # Folders count
    cursor.execute("SELECT COUNT(id) AS total_folders FROM folders WHERE user_id = ? AND is_deleted = 0;", (user_id,))
    total_folders = cursor.fetchone()["total_folders"]

    # Starred count
    cursor.execute("SELECT COUNT(id) AS starred_count FROM files WHERE user_id = ? AND is_deleted = 0 AND is_starred = 1;", (user_id,))
    starred_count = cursor.fetchone()["starred_count"]

    # Trash count
    cursor.execute("SELECT COUNT(id) AS trash_count FROM files WHERE user_id = ? AND is_deleted = 1;", (user_id,))
    trash_count = cursor.fetchone()["trash_count"]

    # File type breakdown (for Recharts donut chart)
    cursor.execute("SELECT extension, file_size FROM files WHERE user_id = ? AND is_deleted = 0 AND status = 'ready';", (user_id,))
    category_counts = {"image": 0, "document": 0, "media": 0, "archive": 0, "code": 0, "other": 0}
    category_bytes = {"image": 0, "document": 0, "media": 0, "archive": 0, "code": 0, "other": 0}

    for row in cursor.fetchall():
        cat = get_file_category(row["extension"])
        category_counts[cat] += 1
        category_bytes[cat] += row["file_size"]

    type_breakdown = [
        {"name": "Images", "category": "image", "count": category_counts["image"], "bytes": category_bytes["image"]},
        {"name": "Documents", "category": "document", "count": category_counts["document"], "bytes": category_bytes["document"]},
        {"name": "Media", "category": "media", "count": category_counts["media"], "bytes": category_bytes["media"]},
        {"name": "Archives", "category": "archive", "count": category_counts["archive"], "bytes": category_bytes["archive"]},
        {"name": "Code", "category": "code", "count": category_counts["code"], "bytes": category_bytes["code"]},
        {"name": "Other", "category": "other", "count": category_counts["other"], "bytes": category_bytes["other"]}
    ]

    return api_success({
        "totalFiles": total_files,
        "totalFolders": total_folders,
        "starredCount": starred_count,
        "trashCount": trash_count,
        "storage": {
            "usedBytes": used_bytes,
            "usedMb": round(used_bytes / (1024 * 1024), 2),
            "quotaBytes": quota_bytes,
            "quotaMb": quota_mb,
            "percentage": min(100.0, round((used_bytes / quota_bytes) * 100, 1)) if quota_bytes > 0 else 0
        },
        "typeBreakdown": type_breakdown
    })

@dashboard_bp.route("/api/dashboard/recent-files", methods=["GET"])
@jwt_required()
def get_recent_files():
    user_id = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, folder_id, original_name, file_size, mime_type, extension, is_starred,
               uploaded_at, last_accessed_at
        FROM files
        WHERE user_id = ? AND is_deleted = 0 AND status = 'ready'
        ORDER BY last_accessed_at DESC, uploaded_at DESC
        LIMIT 10;
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    recent = []
    for r in rows:
        item = dict(r)
        item["category"] = get_file_category(item.get("extension"))
        recent.append(item)

    return api_success({"recentFiles": recent})

@dashboard_bp.route("/api/storage/usage", methods=["GET"])
@jwt_required()
def get_storage_usage():
    user_id = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT storage_quota_mb FROM users WHERE id = ?;", (user_id,))
    quota_mb = cursor.fetchone()["storage_quota_mb"]
    quota_bytes = quota_mb * 1024 * 1024

    cursor.execute("SELECT IFNULL(SUM(file_size), 0) AS used FROM files WHERE user_id = ? AND status = 'ready';", (user_id,))
    used_bytes = cursor.fetchone()["used"]

    # Category breakdown
    cursor.execute("SELECT extension, file_size FROM files WHERE user_id = ? AND is_deleted = 0 AND status = 'ready';", (user_id,))
    categories = {"image": 0, "document": 0, "media": 0, "archive": 0, "code": 0, "other": 0}
    for row in cursor.fetchall():
        cat = get_file_category(row["extension"])
        categories[cat] += row["file_size"]

    # Storage cluster info
    storage = get_storage_backend(
        backend_type=current_app.config["STORAGE_BACKEND"],
        namenode_host=current_app.config["HDFS_NAMENODE_HOST"],
        webhdfs_port=current_app.config["HDFS_WEBHDFS_PORT"],
        base_path=current_app.config["HDFS_BASE_PATH"],
        hdfs_user=current_app.config["HDFS_USER"],
        mock_dir=current_app.config["MOCK_STORAGE_DIR"]
    )
    cluster_metrics = storage.cluster_info()

    return api_success({
        "userQuota": {
            "usedBytes": used_bytes,
            "usedMb": round(used_bytes / (1024 * 1024), 2),
            "quotaBytes": quota_bytes,
            "quotaMb": quota_mb,
            "remainingBytes": max(0, quota_bytes - used_bytes),
            "remainingMb": round(max(0, quota_bytes - used_bytes) / (1024 * 1024), 2),
            "usagePercentage": min(100.0, round((used_bytes / quota_bytes) * 100, 1)) if quota_bytes > 0 else 0
        },
        "breakdown": [
            {"category": "Images", "bytes": categories["image"], "mb": round(categories["image"] / (1024 * 1024), 2)},
            {"category": "Documents", "bytes": categories["document"], "mb": round(categories["document"] / (1024 * 1024), 2)},
            {"category": "Media", "bytes": categories["media"], "mb": round(categories["media"] / (1024 * 1024), 2)},
            {"category": "Archives", "bytes": categories["archive"], "mb": round(categories["archive"] / (1024 * 1024), 2)},
            {"category": "Code", "bytes": categories["code"], "mb": round(categories["code"] / (1024 * 1024), 2)},
            {"category": "Other", "bytes": categories["other"], "mb": round(categories["other"] / (1024 * 1024), 2)}
        ],
        "clusterStorage": cluster_metrics
    })

@dashboard_bp.route("/api/admin/cluster", methods=["GET"])
@jwt_required()
def get_admin_cluster_status():
    jwt_claims = get_jwt()
    if jwt_claims.get("role") != "admin":
        return api_error("FORBIDDEN", "Administrator privileges required to view cluster status.", status_code=403)

    storage = get_storage_backend(
        backend_type=current_app.config["STORAGE_BACKEND"],
        namenode_host=current_app.config["HDFS_NAMENODE_HOST"],
        webhdfs_port=current_app.config["HDFS_WEBHDFS_PORT"],
        base_path=current_app.config["HDFS_BASE_PATH"],
        hdfs_user=current_app.config["HDFS_USER"],
        mock_dir=current_app.config["MOCK_STORAGE_DIR"]
    )

    cluster_data = storage.cluster_info()
    return api_success({
        "backend": current_app.config["STORAGE_BACKEND"],
        "clusterInfo": cluster_data
    })
