from sqlalchemy import Column, DateTime, String, Enum, UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    user = "user"
    chatbot = "chatbot"
    admin = "admin"


# Model Chat History
class UserIds(Base):
    __tablename__ = "ms_user_identity"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default='gen_random_uuid()')
    user_id = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)