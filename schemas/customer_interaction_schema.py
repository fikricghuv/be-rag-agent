from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime

class CustomerInteractionResponse(BaseModel):
    id: UUID4
    conversation_id: UUID4
    customer_id: Optional[UUID4]
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    channel: str
    initial_query: Optional[str]
    total_messages: Optional[int]
    is_handoff_to_agent: Optional[bool]
    agent_id: Optional[UUID4]
    agent_name: Optional[str]
    conversation_status: Optional[str]
    detected_intent: Optional[str]
    main_topic: Optional[str]
    keywords_extracted: Optional[List[str]]
    sentiment_score: Optional[float]
    product_involved: Optional[str]
    customer_feedback_id: Optional[int]
    customer_feedback_score: Optional[int]
    customer_feedback_comment: Optional[str]
    feedback_submitted: Optional[bool]
    others_information: Optional[dict]
    created_at: datetime
    updated_at: datetime

class PaginatedCustomerInteractionResponse(BaseModel):
    total: int
    data: List[CustomerInteractionResponse]

