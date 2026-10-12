"""
Flask Application Factory for MiniCloud Cloud Controller.
Configures:
  - SQLite database handlers & teardown
  - JWT token manager with database-backed token blocklist revocation
  - CORS configuration
  - Rotating file logger in backend/logs/minicloud.log
  - Error handlers enforcing standard JSON error envelopes
  - Route Blueprints
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.config import Config
from app.database import init_db, close_db, get_db
from app.utils.response import api_error

jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Logging setup
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(backend_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "minicloud.log")

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s (%(process)d): %(message)s"
    )
    handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setFormatter(formatter)
    handler.setLevel(getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper()))
    
    app.logger.setLevel(getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper()))
    app.logger.addHandler(handler)

    # 2. CORS
    CORS(app, origins=app.config.get("CORS_ORIGINS", ["http://localhost:5173"]), supports_credentials=True)

    # 3. Database teardown & initialization
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db(app.config["DATABASE_PATH"])

    # 4. JWT Initialization & Blocklist Check
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM token_blocklist WHERE jti = ?;", (jti,))
        return cursor.fetchone() is not None

    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        return api_error("TOKEN_REVOKED", "The token has been revoked. Please log in again.", status_code=401)

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return api_error("TOKEN_EXPIRED", "Token has expired. Please log in again.", status_code=401)

    @jwt.invalid_token_loader
    def invalid_token_response(error_message):
        return api_error("INVALID_TOKEN", f"Invalid token: {error_message}", status_code=401)

    @jwt.unauthorized_loader
    def unauthorized_response(error_message):
        return api_error("UNAUTHORIZED", f"Authorization required: {error_message}", status_code=401)

    # 5. Standard Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return api_error("NOT_FOUND", "The requested resource was not found.", status_code=404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return api_error("METHOD_NOT_ALLOWED", "HTTP method not allowed for this endpoint.", status_code=405)

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return api_error(
            "PAYLOAD_TOO_LARGE",
            f"File exceeds maximum upload size of {app.config.get('MAX_UPLOAD_SIZE_MB')} MB.",
            status_code=413
        )

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error("Unhandled 500 error: %s", str(e))
        return api_error("INTERNAL_SERVER_ERROR", "An unexpected internal error occurred.", status_code=500)

    # 6. Register Blueprints
    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.files import files_bp
    from app.routes.folders import folders_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(dashboard_bp)

    # 7. Serve Built React Frontend (Single-Port LAN Mode)
    from flask import send_from_directory

    frontend_dist = os.path.abspath(
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
    )

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        # Do not intercept API routes
        if path.startswith("api/"):
            return api_error("NOT_FOUND", "Endpoint not found", status_code=404)

        target_file = os.path.join(frontend_dist, path)
        if path != "" and os.path.exists(target_file):
            return send_from_directory(frontend_dist, path)
        
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return send_from_directory(frontend_dist, "index.html")
        
        return jsonify({
            "message": "MiniCloud Cloud Controller API is running.",
            "note": "Frontend build not detected at frontend/dist. Run 'npm run build' inside frontend directory."
        })

    return app
