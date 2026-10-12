"""
MiniCloud Backend Entry Point
Can be run directly via:
  python app.py
or using Waitress production server:
  waitress-serve --host=0.0.0.0 --port=5000 app:app
"""
import os
import sys

# Ensure backend root is on Python sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.factory import create_app
from app.config import Config

app = create_app(Config)

if __name__ == "__main__":
    host = app.config.get("HOST", "0.0.0.0")
    port = app.config.get("PORT", 5000)
    print("=" * 60)
    print(f" Starting MiniCloud Cloud Controller on http://{host}:{port}")
    print(f" Active Storage Backend: [{app.config.get('STORAGE_BACKEND').upper()}]")
    print("=" * 60)
    app.run(host=host, port=port, debug=True)
