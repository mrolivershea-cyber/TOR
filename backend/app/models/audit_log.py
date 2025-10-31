"""
Audit Log model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class AuditLog(Base):
    """Audit log for security events"""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event
    event_type = Column(String(50), index=True, nullable=False)  # login, logout, config_change, etc.
    severity = Column(String(20), default="info")  # info, warning, error, critical
    
    # User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)
    
    # Request info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Details
    message = Column(String(500), nullable=False)
    details = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AuditLog {self.event_type} by {self.username}>"
