from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, LargeBinary, TIMESTAMP, func, BigInteger, UUID
import uuid
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class FileModel(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    uuid_file = Column(UUID(as_uuid=True), unique=True, nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    content = Column(LargeBinary, nullable=False)
    size = Column(BigInteger, nullable=False)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    status = Column(String(50), nullable=False, default="pending")
    