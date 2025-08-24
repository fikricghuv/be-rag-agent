import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database.base import Base

class Prompt(Base):
    __tablename__ = "ms_prompt"
    __table_args__ = {"schema": "ai"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("ai.ms_clients.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), unique=True, index=True, nullable=False)
    name_agent = Column(String(255), nullable=True)
    description_agent = Column(Text, nullable=True)
    style_communication = Column(Text, nullable=False)
    goal = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True) 
    prompt_system = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
