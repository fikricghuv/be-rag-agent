from sqlalchemy import Column, String, DateTime, UUID
from datetime import datetime
import uuid
from database.base import Base

class Client(Base):
    __tablename__ = "ms_clients"
    __table_args__ = {"schema": "ai"}

    # id = Column(Integer, primary_key=True, index=True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)             
    subdomain = Column(String(50), unique=True, nullable=False)  
    api_key = Column(String(255), unique=True, nullable=False)  
    status = Column(String(20), default="active", nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)      
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
