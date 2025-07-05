from sqlalchemy import Column, String, Boolean, DateTime, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
from database.enums.user_role_enum import UserRole

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    # role_id = Column(UUID(as_uuid=True), ForeignKey('ai.ms_role.id'))
    role = Column(
        Enum(UserRole, name='user_role_enum', create_type=True, native_enum=True), # 'user_role_enum' akan menjadi nama tipe di DB
        nullable=False,
        default=UserRole.USER # Default menggunakan anggota Enum
    )
    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}')>"