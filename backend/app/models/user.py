"""
User model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    """User model for authentication"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # 2FA
    totp_secret = Column(String(32))
    totp_enabled = Column(Boolean, default=False)
    
    # Security
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    require_password_change = Column(Boolean, default=False)
    
    # Login tracking
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User {self.username}>"
