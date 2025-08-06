from sqlalchemy import Column, String, Boolean, DateTime, Text, func, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
import uuid
from database.base import Base

class Customer(Base):
    __tablename__ = "dt_customer_profile"
    __table_args__ = {"schema": "ai"}

    customer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("ai.ms_clients.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    phone_number = Column(String(50), unique=True)
    customer_type = Column(String(50))
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    customer_metadata = Column("metadata", JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    conversation_id = Column(UUID(as_uuid=True))
    sender_id = Column(UUID(as_uuid=True))
    source_message = Column(Text)
    other_info = Column(JSON)
    
    model_config = {
        "from_attributes": True
    }