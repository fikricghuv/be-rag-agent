from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class ChatHistoryByNameResponse(BaseModel):
    name: str
    input: str
    output: Optional[str]
    error: Optional[str]
    start_time: datetime

    @field_validator("output", "error")
    def set_default_string(cls, value):
        return value or ""

    class Config:
        from_attributes = True
