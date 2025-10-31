"""
Security utilities and middleware
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import pyotp

from app.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.API_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.API_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, settings.API_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_totp_secret() -> str:
    """Generate a TOTP secret for 2FA"""
    return pyotp.random_base32()


def verify_totp_token(secret: str, token: str) -> bool:
    """Verify a TOTP token"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


def generate_totp_uri(secret: str, username: str) -> str:
    """Generate TOTP URI for QR code"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=username,
        issuer_name=settings.APP_NAME
    )


def generate_export_token() -> str:
    """Generate secure export token"""
    return secrets.token_urlsafe(32)


def hash_export_token(token: str) -> str:
    """Hash export token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def check_ip_whitelist(ip: str, whitelist: Optional[list]) -> bool:
    """Check if IP is in whitelist"""
    if not whitelist:
        return True
    
    from ipaddress import ip_address, ip_network
    
    client_ip = ip_address(ip)
    
    for allowed in whitelist:
        try:
            # Check if it's a network (CIDR)
            if '/' in allowed:
                if client_ip in ip_network(allowed, strict=False):
                    return True
            else:
                # Direct IP comparison
                if client_ip == ip_address(allowed):
                    return True
        except ValueError:
            continue
    
    return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS (only if TLS is enabled)
        if settings.TLS_ENABLE:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.cache: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        client_ip = request.client.host
        now = datetime.utcnow().timestamp()
        
        # Clean old entries
        if client_ip in self.cache:
            self.cache[client_ip] = [
                ts for ts in self.cache[client_ip]
                if now - ts < self.period
            ]
        else:
            self.cache[client_ip] = []
        
        # Check rate limit
        if len(self.cache[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.cache[client_ip].append(now)
        
        return await call_next(request)
