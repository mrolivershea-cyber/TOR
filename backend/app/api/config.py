"""
Configuration management API endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.api.auth import get_current_user
from app.core.config import settings
from app.services.firewall import FirewallService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def get_config(current_user: User = Depends(get_current_user)):
    """Get current configuration"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {
        "tor_pool_size": settings.TOR_POOL_SIZE,
        "tor_base_socks_port": settings.TOR_BASE_SOCKS_PORT,
        "tor_base_ctrl_port": settings.TOR_BASE_CTRL_PORT,
        "tor_countries": settings.TOR_COUNTRIES,
        "tor_strict_nodes": settings.TOR_STRICT_NODES,
        "auto_rotate_enabled": settings.AUTO_ROTATE_ENABLED,
        "auto_rotate_interval": settings.AUTO_ROTATE_INTERVAL,
        "panel_whitelist": settings.PANEL_WHITELIST,
        "socks_whitelist": settings.SOCKS_WHITELIST,
        "firewall_backend": settings.FIREWALL_BACKEND,
        "tls_enable": settings.TLS_ENABLE,
        "domain": settings.DOMAIN,
        "enable_2fa": settings.ENABLE_2FA,
        "export_token_ttl_min": settings.EXPORT_TOKEN_TTL_MIN,
        "export_token_ip_bind": settings.EXPORT_TOKEN_IP_BIND,
    }


@router.put("/whitelist/panel")
async def update_panel_whitelist(
    whitelist: list,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update panel access whitelist"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # TODO: Validate IP addresses/CIDR ranges
    # TODO: Update settings and reload firewall
    
    # Log configuration change
    audit_log = AuditLog(
        event_type="config_change",
        severity="info",
        user_id=current_user.id,
        username=current_user.username,
        message=f"Panel whitelist updated",
        details={"whitelist": whitelist}
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Panel whitelist updated", "whitelist": whitelist}


@router.put("/whitelist/socks")
async def update_socks_whitelist(
    whitelist: list,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update SOCKS access whitelist"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Log configuration change
    audit_log = AuditLog(
        event_type="config_change",
        severity="info",
        user_id=current_user.id,
        username=current_user.username,
        message=f"SOCKS whitelist updated",
        details={"whitelist": whitelist}
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "SOCKS whitelist updated", "whitelist": whitelist}


@router.post("/firewall/apply")
async def apply_firewall(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply firewall rules"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        firewall = FirewallService()
        await firewall.apply_rules()
        
        # Log configuration change
        audit_log = AuditLog(
            event_type="firewall_applied",
            severity="info",
            user_id=current_user.id,
            username=current_user.username,
            message="Firewall rules applied"
        )
        db.add(audit_log)
        await db.commit()
        
        return {"message": "Firewall rules applied successfully"}
        
    except Exception as e:
        logger.error(f"Failed to apply firewall: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply firewall: {str(e)}"
        )
