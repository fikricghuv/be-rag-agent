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

    @field_validator("output", "error")
    def set_default_string(cls, value):
        return value or ""

    class Config:
        from_attributes = True
