from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    created_at: datetime
