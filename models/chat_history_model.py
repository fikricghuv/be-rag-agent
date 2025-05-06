from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    user = "user"
    admin = "admin"

class ChatHistoryResponse(BaseModel):
    id: int
    chat_id: str
    name: str
    role: UserRole
    question: str
    answer: str
    start_time: datetime
    latency: float
    created_at: datetime

class ChatHistoryByNameResponse(BaseModel):
    name: str
    input: str
    output: Optional[str]
    error: Optional[str]
    start_time: datetime

class TotalConversationsResponse(BaseModel):
    total_conversations: int