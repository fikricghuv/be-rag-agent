# schemas.py (Pydantic model yang diperbaiki)

import uuid  
import datetime
from typing import Optional, List, Dict, Any 
from pydantic import BaseModel
from uuid import UUID
from enums.role_enum import RoleEnum

class ChatHistoryResponse(BaseModel):
    id: uuid.UUID  
    room_conversation_id: uuid.UUID 
    sender_id: uuid.UUID 
    message: str  
    created_at: datetime.datetime  
    agent_response_category: Optional[str] = None 
    agent_response_latency: Optional[datetime.timedelta] = None 
    agent_total_tokens: Optional[int] = None 
    agent_input_tokens: Optional[int] = None 
    agent_output_tokens: Optional[int] = None 
    agent_other_metrics: Optional[Dict[str, Any]] = None 
    agent_tools_call: Optional[List[str]] = None 
    role: RoleEnum
    
    model_config = {
        "from_attributes": True
    }

class UserHistoryResponse(BaseModel):
    """
    Respons model untuk riwayat chat user spesifik.
    """
    success: bool
    room_id: UUID
    user_id: UUID
    history: List[ChatHistoryResponse] 

    model_config = {
        "from_attributes": True 
    }