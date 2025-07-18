# schemas/notification_schema.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List

class NotificationItem(BaseModel):
    id: UUID
    message: str
    type: str
    is_read: bool
    is_broadcast: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    success: bool
    total: int
    data: List[NotificationItem]
