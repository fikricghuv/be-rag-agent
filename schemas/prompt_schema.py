from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class PromptResponse(BaseModel):
    id: UUID
    name: str
    name_agent: Optional[str] = None
    description_agent: Optional[str] = None
    style_communication: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PromptUpdate(BaseModel):
    name: str
    name_agent: Optional[str] = None
    description_agent: Optional[str] = None
    style_communication: Optional[str] = None
