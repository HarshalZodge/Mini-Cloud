"""
Health check endpoints for MiniCloud Cloud Controller.
Reports application status, database connectivity, and HDFS storage engine status.
"""
from flask import Blueprint, current_app
from app.database import get_db
from app.utils.response import api_success, api_error
from app.storage import get_storage_backend

health_bp = Blueprint("health", __name__, url_prefix="/api/health")

@health_bp.route("", methods=["GET"])
def check_health():
    """
    General service health check.
    Returns backend mode (hdfs vs mock), database status, and controller uptime.
    """
    # 1. DB check
    db_ok = False
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        db_ok = True
    except Exception as e:
        current_app.logger.error("Health check DB failure: %s", str(e))

    # 2. Storage status
    storage = get_storage_backend(
        backend_type=current_app.config["STORAGE_BACKEND"],
        namenode_host=current_app.config["HDFS_NAMENODE_HOST"],
        webhdfs_port=current_app.config["HDFS_WEBHDFS_PORT"],
        base_path=current_app.config["HDFS_BASE_PATH"],
        hdfs_user=current_app.config["HDFS_USER"],
        mock_dir=current_app.config["MOCK_STORAGE_DIR"]
    )
    storage_health = storage.health()

    status_data = {
        "status": "healthy" if db_ok and storage_health.get("healthy") else "degraded",
        "app": "MiniCloud Cloud Controller",
        "version": "1.0.0",
        "database": "connected" if db_ok else "unreachable",
        "storageBackend": current_app.config["STORAGE_BACKEND"],
        "storageHealth": storage_health
    }
    return api_success(status_data)

@health_bp.route("/hdfs", methods=["GET"])
def check_hdfs():
    """
    Dedicated HDFS cluster health endpoint.
    If HDFS is down or unreachable, returns 503 instead of falling back.
    """
    storage = get_storage_backend(
        backend_type=current_app.config["STORAGE_BACKEND"],
        namenode_host=current_app.config["HDFS_NAMENODE_HOST"],
        webhdfs_port=current_app.config["HDFS_WEBHDFS_PORT"],
        base_path=current_app.config["HDFS_BASE_PATH"],
        hdfs_user=current_app.config["HDFS_USER"],
        mock_dir=current_app.config["MOCK_STORAGE_DIR"]
    )

    health_info = storage.health()
    if not health_info.get("healthy"):
        return api_error(
            code="STORAGE_UNAVAILABLE",
            message=health_info.get("error", "Storage backend is unreachable"),
            status_code=503,
            details=health_info
        )

    # If real HDFS, also query cluster statistics
    cluster_metrics = storage.cluster_info()

    return api_success({
        "backend": current_app.config["STORAGE_BACKEND"],
        "health": health_info,
        "cluster": cluster_metrics
    })
