from sqlalchemy import Column, String, LargeBinary, TIMESTAMP, func, BigInteger, ForeignKey, Integer
import uuid
from sqlalchemy.dialects.postgresql import UUID
from database.base import Base

class FileModel(Base):
    __tablename__ = "dt_uploaded_file"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("ai.ms_clients.id", ondelete="CASCADE"), nullable=False)
    uuid_file = Column(UUID(as_uuid=True), unique=True, nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    content = Column(LargeBinary, nullable=False)
    size = Column(BigInteger, nullable=False)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    status = Column(String(50), nullable=False, default="pending")
    