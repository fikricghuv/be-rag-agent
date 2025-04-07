from sqlalchemy import Column, Integer, Float, Text, DateTime, ARRAY, Numeric, ForeignKey
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
    chat_category = Column(Text, nullable=True)
    input_token = Column(Integer, nullable=True)
    output_token = Column(Integer, nullable=True)
    total_token = Column(Integer, nullable=True)

class ChatHistoryEmbedding(Base):
    __tablename__ = "chat_history_embedding"

    id = Column(Integer, primary_key=True, index=True)
    refidchathistory = Column(Integer, ForeignKey("chat_history.id"), nullable=False)
    embedding_question = Column(ARRAY(Numeric), nullable=False)  # Pastikan ARRAY(Numeric)
    embedding_answer = Column(ARRAY(Numeric), nullable=False)  # Pastikan ARRAY(Numeric)
