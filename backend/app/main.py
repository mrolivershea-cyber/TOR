"""
Main FastAPI application entry point
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.logging import setup_logging
from app.api import api_router
from app.db.session import engine
from app.db.base import Base
from app.services.tor_pool import TorPoolService
from app.services.firewall import FirewallService
from app.core.security import SecurityHeadersMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    logger.info("Starting Tor Proxy Pool application")
    
    # Initialize database tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.info("Admin panel will still be accessible, but database features may not work")
    
    # Initialize services (non-blocking)
    tor_pool = None
    try:
        tor_pool = TorPoolService()
        # Don't block startup - initialize in background
        logger.info(f"Tor pool service created, will initialize {settings.TOR_POOL_SIZE} instances in background")
    except Exception as e:
        logger.warning(f"Tor pool service creation failed: {e}")
    
    # Configure firewall (non-blocking)
    try:
        if settings.FIREWALL_BACKEND != "none":
            firewall = FirewallService()
            # Don't block startup
            logger.info(f"Firewall service created with backend: {settings.FIREWALL_BACKEND}")
    except Exception as e:
        logger.warning(f"Firewall service creation failed: {e}")
    
    logger.info("Application startup complete - admin panel should be accessible")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Tor Proxy Pool")
    if tor_pool:
        try:
            await tor_pool.shutdown()
        except Exception as e:
            logger.error(f"Error during Tor pool shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="Tor Proxy Pool",
    description="Professional Tor SOCKS5 proxy pool management system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Trusted host middleware
if settings.DOMAIN:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[settings.DOMAIN, "localhost", "127.0.0.1"]
    )

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Serve static files for admin panel
static_path = Path(__file__).parent.parent.parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "tor_pool_size": settings.TOR_POOL_SIZE
    }


@app.get("/")
async def root():
    """Root endpoint - Serve admin panel HTML"""
    index_path = Path(__file__).parent.parent.parent / "frontend" / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "Tor Proxy Pool API",
        "version": "1.0.0",
        "docs": "/api/docs" if settings.DEBUG else "disabled"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
