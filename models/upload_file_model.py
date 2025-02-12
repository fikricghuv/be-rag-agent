from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, LargeBinary, TIMESTAMP, func, BIGINT, UUID

# Model database
Base = declarative_base()

# Model File
class FileModel(Base):
    __tablename__ = "uploaded_files"
    id = Column(Integer, primary_key=True, index=True)
    uuid_file = Column(UUID, unique=True, nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    content = Column(LargeBinary, nullable=False)
    size = Column(BIGINT, nullable=False)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())