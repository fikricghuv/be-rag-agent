# app/models/user_id_model.py
from pydantic import BaseModel
from datetime import datetime
from database.models.user_ids_model import UserRole 

class GenerateUserIdRequest(BaseModel):
    """
    Request body untuk menghasilkan user_id.
    Menggunakan Enum UserRole untuk validasi peran yang diperbolehkan.
    """
    role: UserRole 

class UserIdResponse(BaseModel):
    """
    Respons yang berisi user_id yang dihasilkan.
    """
    user_id: str
    role: UserRole
    created_at: datetime


