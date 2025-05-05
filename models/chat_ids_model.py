from sqlalchemy import Column, DateTime, String, Integer, Enum
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

# Definisi Enum untuk Role
class UserRole(enum.Enum):
    user = "user"
    admin = "admin"

# Model Chat History
class ChatIds(Base):
    __tablename__ = "chat_ids"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)