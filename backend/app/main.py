"""
Main FastAPI application entry point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize services
    tor_pool = TorPoolService()
    firewall = FirewallService()
    
    # Start Tor pool
    await tor_pool.initialize(settings.TOR_POOL_SIZE)
    
    # Configure firewall
    if settings.FIREWALL_BACKEND != "none":
        await firewall.apply_rules()
    
    logger.info(f"Tor pool initialized with {settings.TOR_POOL_SIZE} instances")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Tor Proxy Pool")
    await tor_pool.shutdown()


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
    """Root endpoint"""
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
