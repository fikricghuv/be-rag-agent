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
    prompt_system: str
    goal: str
    expected_output: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PromptUpdate(BaseModel):
    name: str
    name_agent: Optional[str] = None
    description_agent: Optional[str] = None
    style_communication: Optional[str] = None
    prompt_system: Optional[str] = None
    goal: Optional[str] = None
    expected_output: Optional[str] = None
