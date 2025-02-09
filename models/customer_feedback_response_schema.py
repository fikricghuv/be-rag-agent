from datetime import datetime
from pydantic import BaseModel

# Schema Response
class CustomerFeedbackResponse(BaseModel):
    id: int
    feedback_from_customer: str
    sentiment: str
    potential_actions: str
    keyword_issue: str
    created_at: datetime

    class Config:
        from_attributes = True