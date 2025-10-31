"""
API routes
"""
from fastapi import APIRouter

from app.api import auth, nodes, config, export, metrics as metrics_routes

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(metrics_routes.router, prefix="/metrics", tags=["metrics"])
