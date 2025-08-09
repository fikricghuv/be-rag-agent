from sqlalchemy import Column, String, Text, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database.base import Base

class WebSourceModel(Base):
    __tablename__ = "dt_web_sources"
    __table_args__ = {"schema": "ai"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)
    source_type = Column(String(50), default="website")
    status = Column(String(50), default="pending")
    last_crawled_at = Column(TIMESTAMP)
    client_id = Column(UUID(as_uuid=True), ForeignKey("ai.ms_clients.id", ondelete="CASCADE"), nullable=False)
    meta_data = Column("metadata", JSON, default={}) 
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    
    class Config:
        orm_mode = True