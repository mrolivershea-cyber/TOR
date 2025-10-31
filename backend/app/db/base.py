"""
Database base classes
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here for Alembic
from app.models.user import User  # noqa
from app.models.tor_node import TorNode  # noqa
from app.models.export_token import ExportToken  # noqa
from app.models.audit_log import AuditLog  # noqa
