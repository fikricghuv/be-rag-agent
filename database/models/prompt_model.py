import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

# Model database
Base = declarative_base()

# Model Prompt
class Prompt(Base):
    __tablename__ = "ms_prompt"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, index=True, nullable=False)
    name_agent = Column(String(255), nullable=True)
    description_agent = Column(Text, nullable=True)
    style_communication = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
