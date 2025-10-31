"""
Tor Node model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON
from sqlalchemy.sql import func

from app.db.base import Base


class TorNode(Base):
    """Tor node/instance model"""
    
    __tablename__ = "tor_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Ports
    socks_port = Column(Integer, unique=True, nullable=False)
    control_port = Column(Integer, unique=True, nullable=False)
    
    # Status
    status = Column(String(20), default="stopped")  # stopped, starting, running, error
    is_healthy = Column(Boolean, default=False)
    
    # Circuit info
    exit_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    exit_country = Column(String(2), nullable=True)  # Country code
    circuit_id = Column(String(50), nullable=True)
    
    # Performance metrics
    latency_ms = Column(Float, nullable=True)
    last_rotation = Column(DateTime, nullable=True)
    rotation_count = Column(Integer, default=0)
    restart_count = Column(Integer, default=0)
    
    # Health check
    failed_checks = Column(Integer, default=0)
    last_check = Column(DateTime, nullable=True)
    
    # Configuration
    countries = Column(JSON, nullable=True)  # Selected countries
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<TorNode {self.node_id} ({self.status})>"
