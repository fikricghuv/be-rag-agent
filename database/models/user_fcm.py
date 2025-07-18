from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.orm import declarative_base

Base = declarative_base()

from database.models.user_model import User

class UserFCM(Base):
    __tablename__ = "user_fcm_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False)

    user = relationship("User", back_populates="fcm_tokens")
