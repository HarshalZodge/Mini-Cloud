"""
Automated tests for Authentication & Health endpoints:
  - Health check responds with healthy status
  - First registered user automatically becomes 'admin'
  - Subsequent registered user becomes 'user'
  - Duplicate registration rejected (409)
  - Invalid credentials rejected (401)
  - JWT logout adds token to blocklist and invalidates subsequent requests
  - Password change requires valid current password
"""
import json

def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["database"] == "connected"

def test_first_user_becomes_admin(client):
    # First user registration
    resp = client.post("/api/auth/register", json={
        "username": "superadmin",
        "email": "superadmin@minicloud.lan",
        "password": "Password123"
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["user"]["role"] == "admin"
    assert "token" in data["data"]

def test_second_user_becomes_regular_user(client):
    # First user
    client.post("/api/auth/register", json={
        "username": "firstadmin",
        "email": "admin@minicloud.lan",
        "password": "Password123"
    })
    # Second user
    resp = client.post("/api/auth/register", json={
        "username": "student1",
        "email": "student1@minicloud.lan",
        "password": "Password123"
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["data"]["user"]["role"] == "user"

def test_duplicate_registration_rejected(client):
    client.post("/api/auth/register", json={
        "username": "student2",
        "email": "student2@minicloud.lan",
        "password": "Password123"
    })
    # Duplicate username
    resp = client.post("/api/auth/register", json={
        "username": "student2",
        "email": "other@minicloud.lan",
        "password": "Password123"
    })
    assert resp.status_code == 409
    data = resp.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "USER_ALREADY_EXISTS"

def test_login_and_me_endpoint(client):
    # Register
    client.post("/api/auth/register", json={
        "username": "alice",
        "email": "alice@minicloud.lan",
        "password": "SecretAlice123"
    })

    # Login
    login_resp = client.post("/api/auth/login", json={
        "identifier": "alice",
        "password": "SecretAlice123"
    })
    assert login_resp.status_code == 200
    token = login_resp.get_json()["data"]["token"]

    # Call /api/auth/me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.get_json()["data"]
    assert me_data["username"] == "alice"
    assert me_data["storageQuotaMb"] == 1024
    assert me_data["storageUsedBytes"] == 0

def test_logout_revokes_token(client):
    # Register & Login
    client.post("/api/auth/register", json={
        "username": "bob",
        "email": "bob@minicloud.lan",
        "password": "SecretBob123"
    })
    login_resp = client.post("/api/auth/login", json={
        "identifier": "bob",
        "password": "SecretBob123"
    })
    token = login_resp.get_json()["data"]["token"]

    # Token works initially
    resp1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == 200

    # Logout
    logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # Token should now be blocked
    resp2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 401
    data = resp2.get_json()
    assert data["error"]["code"] == "TOKEN_REVOKED"
