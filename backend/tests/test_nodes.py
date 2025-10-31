"""
Tests for node management endpoints
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def auth_token():
    """Get authentication token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin"}
        )
        return response.json()["access_token"]


@pytest.mark.asyncio
async def test_list_nodes(auth_token):
    """Test listing all nodes"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/nodes/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_get_stats_summary(auth_token):
    """Test getting stats summary"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/nodes/stats/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_nodes" in data
        assert "healthy_nodes" in data
