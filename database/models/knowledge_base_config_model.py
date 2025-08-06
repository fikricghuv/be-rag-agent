from sqlalchemy import Column, Integer, ForeignKey, UUID
from database.base import Base

class KnowledgeBaseConfigModel(Base):
    __tablename__ = "ms_knowledge_base_config"
    
    id = Column(Integer, primary_key=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("ai.ms_clients.id", ondelete="CASCADE"), nullable=False)
    chunk_size = Column(Integer, nullable=False)
    overlap = Column(Integer, nullable=False)
    num_documents = Column(Integer, nullable=False)