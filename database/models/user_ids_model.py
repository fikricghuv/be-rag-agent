from sqlalchemy import Column, DateTime, String, Enum, UUID, ForeignKey
from datetime import datetime
import enum
from database.base import Base

class UserRole(str, enum.Enum):
    user = "user"
    chatbot = "chatbot"
    admin = "admin"

class UserIds(Base):
    __tablename__ = "ms_user_identity"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default='gen_random_uuid()')
    client_id = Column(UUID(as_uuid=True), ForeignKey("ai.ms_clients.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), nullable=False)
    ref_admin_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)