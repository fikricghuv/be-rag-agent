from pydantic import BaseModel
import uuid
from datetime import datetime

class RoomConversationResponse(BaseModel):
    id: uuid.UUID
    name: str | None = None 
    description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    agent_active: bool

    lastMessage: str | None = None
    lastTimeMessage: datetime | None = None

    class Config:
        orm_mode = True
