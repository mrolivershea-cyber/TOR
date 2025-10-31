"""
Tests for authentication endpoints
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_login_success():
    """Test successful login"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/nodes/")
        assert response.status_code == 403  # No auth header
