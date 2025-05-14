# schemas.py (Pydantic model yang diperbaiki)

import uuid  # Diperlukan untuk tipe UUID
import datetime
from typing import Optional, List, Dict, Any # Diperlukan untuk Optional, List, Dict, Any
from pydantic import BaseModel
from uuid import UUID

class ChatHistoryResponse(BaseModel):
    id: uuid.UUID  # Sesuai dengan Column(Uuid ...)
    room_conversation_id: uuid.UUID # Sesuai dengan Column(Uuid, ForeignKey ...)
    sender_id: uuid.UUID # Sesuai dengan Column(Uuid ...)
    message: str  # Sesuai dengan Column(String ...)
    created_at: datetime.datetime  # Sesuai dengan Column(DateTime ...)
    agent_response_category: Optional[str] = None  # Sesuai dengan Column(String ...) nullable
    agent_response_latency: Optional[datetime.timedelta] = None # Atau Optional[str] jika Anda yakin itu akan jadi string
    agent_total_tokens: Optional[int] = None # Sesuai dengan Column(Integer ...) nullable
    agent_input_tokens: Optional[int] = None # Sesuai dengan Column(Integer ...) nullable
    agent_output_tokens: Optional[int] = None # Sesuai dengan Column(Integer ...) nullable
    agent_other_metrics: Optional[Dict[str, Any]] = None # Sesuai dengan Column(JSON ...) nullable
    agent_tools_call: Optional[List[str]] = None # Sesuai dengan Column(ARRAY(String) ...) nullable

    model_config = {
        "from_attributes": True
    }

class UserHistoryResponse(BaseModel):
    """
    Respons model untuk riwayat chat user spesifik.
    """
    success: bool
    room_id: UUID # Menggunakan tipe UUID
    user_id: UUID
    history: List[ChatHistoryResponse] # Menggunakan list dari ChatHistoryResponse

    model_config = {
        "from_attributes": True  # <- wajib untuk load dari SQLAlchemy model
    }