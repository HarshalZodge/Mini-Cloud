"""
Pytest configuration and fixtures for MiniCloud tests.
Creates isolated in-memory or temporary file SQLite database for each test session.
"""
import pytest
import os
import sys
import tempfile
import shutil

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.factory import create_app
from app.config import Config
from app.storage import reset_storage_backend

class TestConfig(Config):
    TESTING = True
    JWT_SECRET_KEY = "test-jwt-secret-key-382910"
    STORAGE_BACKEND = "mock"

@pytest.fixture
def app():
    # Setup temporary directory for test DB and mock storage
    temp_dir = tempfile.mkdtemp()
    test_db = os.path.join(temp_dir, "test_minicloud.db")
    test_storage = os.path.join(temp_dir, "test_storage")

    class RuntimeTestConfig(TestConfig):
        DATABASE_PATH = test_db
        MOCK_STORAGE_DIR = test_storage

    reset_storage_backend()
    app = create_app(RuntimeTestConfig)

    yield app

    # Teardown
    reset_storage_backend()
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def client(app):
    return app.test_client()
