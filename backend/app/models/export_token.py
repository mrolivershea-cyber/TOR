"""
Export Token model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class ExportToken(Base):
    """Export token for sharing proxy lists"""
    
    __tablename__ = "export_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    
    # Creator
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # IP binding
    bound_ip = Column(String(45), nullable=True)  # If IP_BIND is enabled
    
    # Validity
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    use_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    
    # Metadata
    description = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ExportToken {self.id} (revoked={self.is_revoked})>"
