from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, Boolean
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.sql import func
from database.base import Base

class Member(Base):
    __tablename__ = "members"
    __table_args__ = {"schema": "ai"}

    id = Column(Uuid, primary_key=True, default=uuid.uuid4) 
    room_conversation_id = Column(Uuid, ForeignKey("ai.room_conversation.id", ondelete="CASCADE"), nullable=False) # Use Uuid
    user_id = Column(Uuid, nullable=False)  
    role = Column(String(20), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_online = Column(Boolean, default=False, nullable=False)

    # relationship dengan tabel room_conversation
    room_conversation = relationship("RoomConversation", back_populates="members")

    def __repr__(self):
        return f"<Member(user_id='{self.user_id}', role='{self.role}')>"
