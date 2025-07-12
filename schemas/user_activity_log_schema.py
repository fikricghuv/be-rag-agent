from pydantic import BaseModel
from typing import Optional, Union
from uuid import UUID
from datetime import datetime

class UserActivityLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    endpoint: Optional[str]
    method: Optional[str]
    request_data: Optional[dict]
    response_data: Optional[Union[dict, list]]
    status_code: Optional[int]
    timestamp: datetime

    class Config:
        from_attributes = True
