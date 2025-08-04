from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Text, DateTime, String, ARRAY, Boolean, Numeric, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB

Base = declarative_base()

class CustomerInteraction(Base):
    __tablename__ = "dt_customer_interactions"
    __table_args__ = {"schema": "ai"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai.dt_room_conversation.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    channel = Column(String, nullable=False)
    initial_query = Column(Text)
    total_messages = Column(Integer)
    is_handoff_to_agent = Column(Boolean, default=False)
    agent_id = Column(UUID(as_uuid=True))
    agent_name = Column(String)
    conversation_status = Column(String)
    detected_intent = Column(String)
    main_topic = Column(String)
    keywords_extracted = Column(ARRAY(Text))
    sentiment_score = Column(Numeric(3, 2))
    product_involved = Column(String)
    customer_feedback_id = Column(Integer, ForeignKey("ai.dt_customer_feedback.id"))
    customer_feedback_score = Column(Integer)
    customer_feedback_comment = Column(Text)
    feedback_submitted = Column(Boolean, default=False)
    others_information = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"))
