from sqlalchemy import Column, DateTime, String, Integer, Enum, UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

# Definisi Enum untuk Role
class UserRole(enum.Enum):
    user = "user"
    admin = "admin"
    chatbot = "chatbot"

# Model Chat History
class UserIds(Base):
    __tablename__ = "user_id"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default='gen_random_uuid()')
    user_id = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)