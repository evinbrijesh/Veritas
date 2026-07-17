"""
Relational models — investigator accounts, roles, and the audit trail.
Lives in Postgres, separate from Neo4j (which only holds the evidence
knowledge graph). Chain-of-custody requires knowing exactly WHO touched
WHAT evidence WHEN, which is why every sensitive action writes an
AuditLog row.
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Role(str, enum.Enum):
    ANALYST = "analyst"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"
    ADMIN = "admin"


class Investigator(Base):
    __tablename__ = "investigators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    badge_id = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.ANALYST)
    department = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(String, default=True)

    audit_entries = relationship("AuditLog", back_populates="investigator")


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("investigators.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="open")  # open, under_review, closed


class AuditLog(Base):
    """
    Immutable-by-convention audit trail. Every evidence view, export,
    or pipeline run gets a row here. This table is what makes VERITAS's
    output defensible in a tribunal — never delete from it.
    """
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigator_id = Column(UUID(as_uuid=True), ForeignKey("investigators.id"))
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    action = Column(String, nullable=False)       # e.g. "VIEWED_EVIDENCE", "RAN_PIPELINE", "EXPORTED_REPORT"
    target_reference = Column(String, nullable=True)  # evidence file id, report id, etc.
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)

    investigator = relationship("Investigator", back_populates="audit_entries")
