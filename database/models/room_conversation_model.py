from sqlalchemy import Column, String, DateTime, Uuid, Boolean # Import Uuid
from sqlalchemy.orm import relationship
from database.base import Base
import uuid
from sqlalchemy.sql import func

class RoomConversation(Base):
    __tablename__ = "dt_room_conversation"
    __table_args__ = {"schema": "ai"}

    id = Column(Uuid, primary_key=True, default=uuid.uuid4) 
    name = Column(String(255))
    description = Column(String)
    status = Column(String(20), nullable=False, default='open')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    agent_active = Column(Boolean, default=True, nullable=False)

    # relationship dengan tabel Member dan Chat
    members = relationship("Member", back_populates="room_conversation", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="room_conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RoomConversation(id='{self.id}', name='{self.name}', status='{self.status}')>"
