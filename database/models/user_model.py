from sqlalchemy import (
    Column, String, Boolean, DateTime, TIMESTAMP, ForeignKey, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import uuid
from datetime import datetime
from database.enums.user_role_enum import UserRole

Base = declarative_base()

class User(Base):
    __tablename__ = "ms_admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    role = Column(
        Enum(UserRole, name='user_role_enum', create_type=True, native_enum=True),
        nullable=False,
        default=UserRole.USER
    )

    # Relasi ke UserFCM
    fcm_tokens = relationship("UserFCM", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}')>"

class UserFCM(Base):
    __tablename__ = "dt_user_fcm_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("ms_admin_users.id"), nullable=False)
    token = Column(String, nullable=False)

    # Relasi ke User
    user = relationship("User", back_populates="fcm_tokens")
