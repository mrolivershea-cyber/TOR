"""
Authentication API endpoints
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import qrcode
import io
import base64

from app.db.session import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_secret,
    verify_totp_token,
    generate_totp_uri,
)
from app.core.config import settings
from app.services.alerts import AlertService

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
alert_service = AlertService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = decode_token(token)
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


@router.post("/login")
async def login(
    request: Request,
    username: str,
    password: str,
    totp_token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Login endpoint"""
    
    # Get user
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        # Log failed attempt
        audit_log = AuditLog(
            event_type="login_failed",
            severity="warning",
            username=username,
            ip_address=request.client.host,
            message=f"Login failed: user not found"
        )
        db.add(audit_log)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until}"
        )
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        # Increment failed attempts
        user.failed_login_attempts += 1
        
        # Lock account if too many attempts
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
            
            # Send alert
            await alert_service.alert_brute_force(
                request.client.host,
                username,
                user.failed_login_attempts
            )
        
        # Log failed attempt
        audit_log = AuditLog(
            event_type="login_failed",
            severity="warning",
            user_id=user.id,
            username=username,
            ip_address=request.client.host,
            message=f"Login failed: incorrect password (attempt {user.failed_login_attempts})"
        )
        db.add(audit_log)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify 2FA if enabled
    if settings.ENABLE_2FA and user.totp_enabled:
        if not totp_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA token required"
            )
        
        if not verify_totp_token(user.totp_secret, totp_token):
            # Log failed 2FA
            audit_log = AuditLog(
                event_type="2fa_failed",
                severity="warning",
                user_id=user.id,
                username=username,
                ip_address=request.client.host,
                message="2FA verification failed"
            )
            db.add(audit_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA token"
            )
    
    # Reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    
    # Log successful login
    audit_log = AuditLog(
        event_type="login_success",
        severity="info",
        user_id=user.id,
        username=username,
        ip_address=request.client.host,
        message="Login successful"
    )
    db.add(audit_log)
    await db.commit()
    
    # Create tokens
    access_token = create_access_token({"sub": user.username})
    refresh_token = create_refresh_token({"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "require_password_change": user.require_password_change
    }


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    
    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    current_user.require_password_change = False
    
    # Log password change
    audit_log = AuditLog(
        event_type="password_changed",
        severity="info",
        user_id=current_user.id,
        username=current_user.username,
        message="Password changed successfully"
    )
    db.add(audit_log)
    await db.commit()
    
    logger.info(f"Password changed for user {current_user.username}")
    
    return {"message": "Password changed successfully"}


@router.post("/setup-2fa")
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Setup 2FA for user"""
    
    if not settings.ENABLE_2FA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    # Generate TOTP secret
    secret = generate_totp_secret()
    current_user.totp_secret = secret
    
    # Generate QR code
    uri = generate_totp_uri(secret, current_user.username)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    await db.commit()
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_code_base64}",
        "uri": uri
    }


@router.post("/verify-2fa")
async def verify_2fa(
    totp_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify and enable 2FA"""
    
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not set up"
        )
    
    if not verify_totp_token(current_user.totp_secret, totp_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP token"
        )
    
    current_user.totp_enabled = True
    
    # Log 2FA enabled
    audit_log = AuditLog(
        event_type="2fa_enabled",
        severity="info",
        user_id=current_user.id,
        username=current_user.username,
        message="2FA enabled successfully"
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "2FA enabled successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "totp_enabled": current_user.totp_enabled,
        "require_password_change": current_user.require_password_change,
        "last_login": current_user.last_login
    }
