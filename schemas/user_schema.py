from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from database.enums.user_role_enum import UserRole

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    role: str = None

    class Config:
        from_attributes = True
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., min_length=8, example="S3cur3P@ssw0rd")
    full_name: Optional[str] = Field(None, example="John Doe")
    role: Optional[UserRole] = Field(UserRole.USER, example="user")
