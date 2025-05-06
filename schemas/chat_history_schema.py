from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class ChatHistoryResponse(BaseModel):
    id: int
    name: str
    input: str
    output: Optional[str]
    error: Optional[str]
    start_time: datetime
    latency: float
    agent_name: Optional[str]
    chat_category: Optional[str]
    input_token: Optional[int]
    output_token: Optional[int]
    total_token: Optional[int]

    @field_validator("output", "error")
    def set_default_string(cls, value):
        return value or ""
    
    @field_validator("agent_name")
    def set_default_name(cls, value):
        return value or "Unknown"
    
    @field_validator("chat_category")
    def set_default_chat_category(cls, value):
        return value or "Uncategorized"
    
    @field_validator("input_token", "output_token", "total_token")
    def set_default_token(cls, value):
        return value or 0

    class Config:
        from_attributes = True
