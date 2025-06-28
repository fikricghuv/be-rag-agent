from datetime import datetime
from pydantic import BaseModel

class CustomerFeedbackResponse(BaseModel):
    feedback_from_customer: str
    sentiment: str
    potential_actions: str
    keyword_issue: str
    category: str
    product_name: str
    created_at: datetime

    class Config:
        from_attributes = True
        
class CategoryFrequencyResponse(BaseModel):
    category: str
    frequency: int