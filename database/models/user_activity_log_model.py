from sqlalchemy import Column, DateTime, String, UUID, Integer, JSON
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from uuid import uuid4

Base = declarative_base()

class UserActivityLog(Base):
    __tablename__ = "dt_user_activity_log"
    __table_args__ = {"schema": "ai"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    endpoint = Column(String)
    method = Column(String)
    request_data = Column(JSON)
    response_data = Column(JSON)
    status_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

