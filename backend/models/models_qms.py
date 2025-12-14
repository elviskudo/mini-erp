from sqlalchemy import Column, String, Integer, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
import enum
from database import Base


class DocStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    OBSOLETE = "OBSOLETE"


class SOPDocument(Base):
    __tablename__ = "sop_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    version = Column(Integer, default=1)
    status = Column(Enum(DocStatus), default=DocStatus.DRAFT)
    
    file_url = Column(String, nullable=True)  # Link to PDF
    content = Column(String, nullable=True)   # Or markdown content
    
    created_by = Column(String)  # User ID or Name
    approved_by = Column(String, nullable=True)
    
    effective_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
