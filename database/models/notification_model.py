from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "ai"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    receiver_id = Column(UUID(as_uuid=True), nullable=True) 
    message = Column(String, nullable=False)
    type = Column(String, nullable=False, default="chat") 
    is_broadcast = Column(Boolean, nullable=False, default=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, broadcast={self.is_broadcast})>"
    
    
