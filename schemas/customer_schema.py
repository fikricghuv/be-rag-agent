# schemas/customer_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime
from uuid import UUID

class CustomerBase(BaseModel):
    full_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    customer_type: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    metadata: Optional[Any]
    other_info: Optional[Any]
    is_active: Optional[bool] = True

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(CustomerBase):
    pass

class CustomerOut(CustomerBase):
    customer_id: UUID
    registration_date: Optional[datetime]
    last_activity_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    conversation_id: Optional[UUID]
    sender_id: Optional[UUID]
    source_message: Optional[str]

    # class Config:
    #     orm_mode = True
    
    model_config = {
        "from_attributes": True
    }

class CustomerResponse(BaseModel):
    customer_id: UUID
    full_name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    customer_type: Optional[str]
    registration_date: Optional[datetime]
    last_activity_at: Optional[datetime]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    customer_metadata: Optional[dict]
    is_active: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    conversation_id: Optional[UUID]
    sender_id: Optional[UUID]
    source_message: Optional[str]
    other_info: Optional[dict]
    
    # class Config:
    #     orm_mode = True

    model_config = {
        "from_attributes": True
    }


