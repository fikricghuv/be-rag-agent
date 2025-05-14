from pydantic import BaseModel
import uuid
from datetime import datetime

class RoomConversationResponse(BaseModel):
    """
    Pydantic model for RoomConversation response.
    """
    id: uuid.UUID # Sesuaikan tipe data Pydantic dengan tipe data SQLAlchemy
    name: str | None = None # Gunakan Optional[str] atau str | None untuk kolom nullable
    status: str
    created_at: datetime

    class Config:
        # Mengaktifkan ORM mode agar Pydantic bisa membaca data dari objek SQLAlchemy
        orm_mode = True