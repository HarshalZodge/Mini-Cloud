"""
Waitress production WSGI server launcher for MiniCloud
"""
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.factory import create_app
from app.config import Config
from waitress import serve

application = create_app(Config)

if __name__ == "__main__":
    host = Config.HOST
    port = Config.PORT
    print("=" * 60)
    print(f" Starting MiniCloud Production Server (Waitress)")
    print(f" URL: http://{host}:{port}")
    print(f" Active Storage Backend: [{Config.STORAGE_BACKEND.upper()}]")
    print("=" * 60)
    serve(application, host=host, port=port, threads=8)
