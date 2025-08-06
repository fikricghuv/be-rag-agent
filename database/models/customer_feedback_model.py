from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, UUID
from datetime import datetime
from database.base import Base

class CustomerFeedback(Base):
    __tablename__ = "dt_customer_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("ai.ms_clients.id", ondelete="CASCADE"), nullable=False)
    feedback_from_customer = Column(Text, nullable=False)
    sentiment = Column(Text, nullable=False)
    potential_actions = Column(Text, nullable=False)
    keyword_issue = Column(Text, nullable=False)
    category = Column(Text, nullable=True)
    product_name = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)