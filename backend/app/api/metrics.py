"""
Metrics API endpoints (not Prometheus)
"""
import logging
from fastapi import APIRouter, Depends

from app.models.user import User
from app.api.auth import get_current_user
from app.services.tor_pool import TorPoolService

logger = logging.getLogger(__name__)
router = APIRouter()

tor_pool = TorPoolService()


@router.get("/")
async def get_metrics(current_user: User = Depends(get_current_user)):
    """Get application metrics"""
    
    nodes = await tor_pool.get_all_status()
    
    total = len(nodes)
    healthy = sum(1 for n in nodes if n.get('is_healthy', False))
    
    return {
        "nodes": {
            "total": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "health_percentage": (healthy / total * 100) if total > 0 else 0
        }
    }
