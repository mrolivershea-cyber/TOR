"""
Export tokens and proxy list API endpoints
"""
import logging
import csv
import json
from datetime import datetime, timedelta
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.export_token import ExportToken
from app.api.auth import get_current_user
from app.core.security import generate_export_token, hash_export_token, check_ip_whitelist
from app.core.config import settings
from app.services.tor_pool import TorPoolService

logger = logging.getLogger(__name__)
router = APIRouter()

tor_pool = TorPoolService()


@router.post("/tokens")
async def create_export_token(
    description: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new export token"""
    
    # Generate token
    token = generate_export_token()
    token_hash = hash_export_token(token)
    
    # Calculate expiry
    expires_at = datetime.utcnow() + timedelta(minutes=settings.EXPORT_TOKEN_TTL_MIN)
    
    # Create token record
    export_token = ExportToken(
        token_hash=token_hash,
        user_id=current_user.id,
        expires_at=expires_at,
        description=description
    )
    
    db.add(export_token)
    await db.commit()
    await db.refresh(export_token)
    
    logger.info(f"Export token created by {current_user.username}")
    
    return {
        "token": token,
        "expires_at": expires_at,
        "description": description
    }


@router.get("/tokens")
async def list_export_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all export tokens for current user"""
    
    result = await db.execute(
        select(ExportToken)
        .where(ExportToken.user_id == current_user.id)
        .order_by(ExportToken.created_at.desc())
    )
    tokens = result.scalars().all()
    
    return {
        "tokens": [
            {
                "id": t.id,
                "description": t.description,
                "expires_at": t.expires_at,
                "is_revoked": t.is_revoked,
                "use_count": t.use_count,
                "last_used": t.last_used,
                "created_at": t.created_at
            }
            for t in tokens
        ]
    }


@router.delete("/tokens/{token_id}")
async def revoke_export_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an export token"""
    
    result = await db.execute(
        select(ExportToken)
        .where(ExportToken.id == token_id)
        .where(ExportToken.user_id == current_user.id)
    )
    token = result.scalar_one_or_none()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    token.is_revoked = True
    token.revoked_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Export token {token_id} revoked by {current_user.username}")
    
    return {"message": "Token revoked successfully"}


async def verify_export_token(
    request: Request,
    token: str,
    db: AsyncSession
) -> ExportToken:
    """Verify export token"""
    
    token_hash = hash_export_token(token)
    
    result = await db.execute(
        select(ExportToken).where(ExportToken.token_hash == token_hash)
    )
    export_token = result.scalar_one_or_none()
    
    if not export_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    if export_token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    if export_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    
    # Check IP binding
    if settings.EXPORT_TOKEN_IP_BIND and export_token.bound_ip:
        if request.client.host != export_token.bound_ip:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token is bound to a different IP"
            )
    
    # Update usage stats
    export_token.use_count += 1
    export_token.last_used = datetime.utcnow()
    await db.commit()
    
    return export_token


@router.get("/download/txt")
async def export_txt(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Export proxy list as TXT"""
    
    await verify_export_token(request, token, db)
    
    # Get nodes
    nodes = await tor_pool.get_all_status()
    
    # Generate TXT
    lines = []
    for node in nodes:
        if node.get('is_healthy'):
            lines.append(f"127.0.0.1:{node['socks_port']}")
    
    content = '\n'.join(lines)
    
    return PlainTextResponse(
        content=content,
        headers={
            'Content-Disposition': 'attachment; filename="proxies.txt"'
        }
    )


@router.get("/download/csv")
async def export_csv(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Export proxy list as CSV"""
    
    await verify_export_token(request, token, db)
    
    # Get nodes
    nodes = await tor_pool.get_all_status()
    
    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['host', 'port', 'exit_ip', 'exit_country', 'is_healthy'])
    
    # Data
    for node in nodes:
        writer.writerow([
            '127.0.0.1',
            node['socks_port'],
            node.get('exit_ip', ''),
            node.get('exit_country', ''),
            node.get('is_healthy', False)
        ])
    
    content = output.getvalue()
    
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={
            'Content-Disposition': 'attachment; filename="proxies.csv"'
        }
    )


@router.get("/download/json")
async def export_json(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Export proxy list as JSON"""
    
    await verify_export_token(request, token, db)
    
    # Get nodes
    nodes = await tor_pool.get_all_status()
    
    # Generate JSON
    proxies = []
    for node in nodes:
        proxies.append({
            'host': '127.0.0.1',
            'port': node['socks_port'],
            'exit_ip': node.get('exit_ip'),
            'exit_country': node.get('exit_country'),
            'is_healthy': node.get('is_healthy', False)
        })
    
    return {
        "proxies": proxies,
        "total": len(proxies),
        "timestamp": datetime.utcnow().isoformat()
    }
