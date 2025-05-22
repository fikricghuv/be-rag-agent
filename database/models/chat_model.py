from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid, Integer, Interval, JSON, ARRAY
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.sql import func
from database.base import Base


class Chat(Base):
    __tablename__ = "chats"
    __table_args__ = {"schema": "ai"}

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    room_conversation_id = Column(Uuid, ForeignKey("ai.room_conversation.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Uuid, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    agent_response_category = Column(String(255))
    agent_response_latency = Column(Interval)
    agent_total_tokens = Column(Integer)
    agent_input_tokens = Column(Integer)
    agent_output_tokens = Column(Integer)
    agent_other_metrics = Column(JSON)
    agent_tools_call = Column(ARRAY(String))
    role = Column(String(255), nullable=False)

    # relationship dengan tabel room_conversation 
    room_conversation = relationship("RoomConversation", back_populates="chats")

    def __repr__(self):
        return f"<Chat(sender_id='{self.sender_id}', message='{self.message}')>"
