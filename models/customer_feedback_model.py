from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Text, DateTime
from datetime import datetime

# Model database
Base = declarative_base()

# Model Customer Feedback
class CustomerFeedback(Base):
    __tablename__ = "customer_feedback"
    id = Column(Integer, primary_key=True, index=True)
    feedback_from_customer = Column(Text, nullable=False)
    sentiment = Column(Text, nullable=False)
    potential_actions = Column(Text, nullable=False)
    keyword_issue = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)