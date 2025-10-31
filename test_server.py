#!/usr/bin/env python3
"""
Simple test server to verify admin panel works
Run with: python3 test_server.py

Requirements: pip3 install fastapi uvicorn
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import uvicorn

app = FastAPI(title="Connexa Proxy - Test Mode")

# Serve static files
static_path = Path(__file__).parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    print(f"✓ Static files mounted from: {static_path}")
else:
    print(f"✗ Static files not found at: {static_path}")

@app.get("/")
async def root():
    """Serve admin panel"""
    index_path = Path(__file__).parent / "frontend" / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Admin panel not found", "path": str(index_path)}

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "mode": "test", "message": "Test server running"}

@app.post("/api/v1/auth/login")
async def test_login(request: Request):
    """Test login endpoint"""
    try:
        # Try JSON first
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
    except:
        # Try form data
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
        except:
            return JSONResponse({"detail": "Invalid request format"}, status_code=400)
    
    print(f"Login attempt: {username}")
    if username == "admin" and password == "admin":
        return {
            "access_token": "test_token_12345_this_is_not_secure",
            "token_type": "bearer",
            "require_password_change": False
        }
    return JSONResponse({"detail": "Invalid credentials"}, status_code=401)

@app.get("/api/v1/auth/me")
async def test_me():
    """Current user endpoint"""
    return {
        "username": "admin",
        "is_admin": True,
        "require_password_change": False
    }

@app.get("/api/v1/nodes/stats/summary")
async def test_stats():
    """Test stats endpoint"""
    return {
        "total_nodes": 5,
        "healthy_nodes": 4,
        "unhealthy_nodes": 1,
        "health_percentage": 80.0,
        "countries": {"US": 2, "DE": 2, "FR": 1}
    }

@app.get("/api/v1/nodes/")
async def test_nodes():
    """Test nodes list with enhanced status"""
    return {
        "total": 5,
        "nodes": [
            {
                "node_id": "tor-0000",
                "socks_port": 30000,
                "control_port": 40000,
                "is_healthy": True,
                "status": "healthy",
                "exit_ip": "185.220.101.1",
                "country": "DE",
                "exit_country": "DE",
                "server_ip": "195.26.255.18",
                "latency_ms": 120
            },
            {
                "node_id": "tor-0001",
                "socks_port": 30001,
                "control_port": 40001,
                "is_healthy": True,
                "status": "healthy",
                "exit_ip": "185.220.101.2",
                "country": "US",
                "exit_country": "US",
                "server_ip": "195.26.255.18",
                "latency_ms": 95
            },
            {
                "node_id": "tor-0002",
                "socks_port": 30002,
                "control_port": 40002,
                "is_healthy": False,
                "status": "unhealthy",
                "exit_ip": None,
                "country": None,
                "exit_country": None,
                "server_ip": "195.26.255.18",
                "latency_ms": None
            },
            {
                "node_id": "tor-0003",
                "socks_port": 30003,
                "control_port": 40003,
                "is_healthy": True,
                "status": "slow",
                "exit_ip": "185.220.101.3",
                "country": "GB",
                "exit_country": "GB",
                "server_ip": "195.26.255.18",
                "latency_ms": 650
            },
            {
                "node_id": "tor-0004",
                "socks_port": 30004,
                "control_port": 40004,
                "is_healthy": True,
                "status": "rotating",
                "exit_ip": "185.220.101.4",
                "country": "FR",
                "exit_country": "FR",
                "server_ip": "195.26.255.18",
                "latency_ms": 110
            }
        ]
    }

@app.post("/api/v1/nodes/rotate")
async def test_rotate_all():
    """Test rotate all"""
    return {"message": "All circuits rotated", "success": True}

@app.post("/api/v1/nodes/{node_id}/rotate")
async def test_rotate_node(node_id: str):
    """Test rotate single node"""
    return {"message": f"Circuit rotated for {node_id}", "success": True}

@app.post("/api/v1/nodes/scale")
async def test_scale(new_size: int):
    """Test scale"""
    return {"message": f"Pool scaled to {new_size} nodes", "success": True}

@app.get("/api/v1/config/")
async def test_config():
    """Test config"""
    return {
        "tor_pool_size": 5,
        "tor_base_socks_port": 30000,
        "tor_countries": ["US", "DE"],
        "auto_rotate_enabled": True,
        "firewall_backend": "test",
        "tls_enable": False,
        "domain": None
    }

@app.post("/api/v1/config/firewall/apply")
async def test_firewall():
    """Test firewall"""
    return {"message": "Firewall rules applied", "success": True}

@app.get("/api/v1/export/tokens")
async def test_tokens():
    """Test tokens list"""
    return {
        "tokens": [
            {
                "id": 1,
                "description": "Test Token",
                "expires_at": "2025-12-31T23:59:59",
                "is_revoked": False,
                "use_count": 5
            }
        ]
    }

@app.post("/api/v1/export/tokens")
async def test_create_token(request: Request):
    """Test create token"""
    try:
        data = await request.json()
        description = data.get("description")
    except:
        try:
            form = await request.form()
            description = form.get("description")
        except:
            description = None
    
    return {
        "token": "test_export_token_1234567890abcdef",
        "expires_at": "2025-12-31T23:59:59",
        "description": description or "Test Token"
    }

@app.delete("/api/v1/export/tokens/{token_id}")
async def test_revoke_token(token_id: int):
    """Test revoke token"""
    return {"message": "Token revoked", "success": True}

@app.post("/api/v1/config/tor/countries")
async def test_set_countries(request: Request):
    """Test set exit countries endpoint"""
    data = await request.json()
    countries = data.get("countries", "US,DE")
    print(f"Setting exit countries to: {countries}")
    return {
        "message": f"Exit countries set to: {countries}",
        "countries": countries.split(','),
        "strict_nodes": data.get("strict_nodes", True),
        "success": True
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔐 Connexa Proxy - TEST SERVER")
    print("="*60)
    print("\nThis is a test server to verify the admin panel works.")
    print("It does NOT provide actual Tor proxy functionality.")
    print("\nAccess the admin panel at:")
    print("  → http://localhost:8000")
    print("  → http://0.0.0.0:8000")
    print("\nDefault credentials:")
    print("  Username: admin")
    print("  Password: admin")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
