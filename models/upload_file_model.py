from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, LargeBinary, TIMESTAMP, func

# Model database
Base = declarative_base()

# Model File
class FileModel(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content = Column(LargeBinary, nullable=False)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())