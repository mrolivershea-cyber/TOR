"""
Tor nodes management API endpoints
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.services.tor_pool import TorPoolService

logger = logging.getLogger(__name__)
router = APIRouter()

# Global Tor pool service instance
tor_pool = TorPoolService()


@router.get("/")
async def list_nodes(current_user: User = Depends(get_current_user)):
    """List all Tor nodes"""
    nodes = await tor_pool.get_all_status()
    return {
        "total": len(nodes),
        "nodes": nodes
    }


@router.get("/{node_id}")
async def get_node(
    node_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific node status"""
    try:
        node = await tor_pool.get_node_status(node_id)
        return node
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/rotate")
async def rotate_all_nodes(current_user: User = Depends(get_current_user)):
    """Rotate all Tor circuits (NEWNYM)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    await tor_pool.rotate_all()
    
    logger.info(f"All circuits rotated by {current_user.username}")
    
    return {"message": "All circuits rotated successfully"}


@router.post("/{node_id}/rotate")
async def rotate_node(
    node_id: str,
    current_user: User = Depends(get_current_user)
):
    """Rotate specific Tor circuit"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        await tor_pool.rotate_node(node_id)
        logger.info(f"Circuit rotated for {node_id} by {current_user.username}")
        return {"message": f"Circuit rotated for {node_id}"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/scale")
async def scale_pool(
    new_size: int,
    current_user: User = Depends(get_current_user)
):
    """Scale Tor pool to new size"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if new_size < 1 or new_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pool size must be between 1 and 100"
        )
    
    await tor_pool.scale(new_size)
    
    logger.info(f"Pool scaled to {new_size} by {current_user.username}")
    
    return {
        "message": f"Pool scaled to {new_size} nodes",
        "new_size": new_size
    }


@router.get("/stats/summary")
async def get_stats_summary(current_user: User = Depends(get_current_user)):
    """Get summary statistics"""
    nodes = await tor_pool.get_all_status()
    
    total = len(nodes)
    healthy = sum(1 for n in nodes if n.get('is_healthy', False))
    unhealthy = total - healthy
    
    # Count by country
    countries = {}
    for node in nodes:
        country = node.get('exit_country')
        if country:
            countries[country] = countries.get(country, 0) + 1
    
    return {
        "total_nodes": total,
        "healthy_nodes": healthy,
        "unhealthy_nodes": unhealthy,
        "health_percentage": (healthy / total * 100) if total > 0 else 0,
        "countries": countries
    }
