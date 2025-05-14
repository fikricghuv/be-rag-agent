from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()
class KnowledgeBaseConfigModel(Base):
    __tablename__ = "knowledge_base_config"
    id = Column(Integer, primary_key=True)
    chunk_size = Column(Integer, nullable=False)
    overlap = Column(Integer, nullable=False)
    num_documents = Column(Integer, nullable=False)