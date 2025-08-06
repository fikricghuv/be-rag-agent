from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
from database.base import Base

class Notification(Base):
    __tablename__ = "dt_notifications"
    __table_args__ = {"schema": "ai"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("ai.ms_clients.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), nullable=True) 
    message = Column(String, nullable=False)
    type = Column(String, nullable=False, default="chat") 
    is_broadcast = Column(Boolean, nullable=False, default=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, broadcast={self.is_broadcast})>"
    
    
