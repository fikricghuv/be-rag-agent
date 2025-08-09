from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

class WebsiteKBInfo(BaseModel):
    id: UUID
    url: str
    status: str
    created_at: datetime

class WebsiteKBCreateResponse(BaseModel):
    message: str
    url: str

class WebsiteUrlPayload(BaseModel):
    url: str
