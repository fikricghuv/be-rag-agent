from sqlalchemy import Column, Integer, Float, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()
# Model Chat History
class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    input = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    latency = Column(Float, nullable=False)
    agent_name = Column(Text, nullable=False)
