from pydantic import BaseModel

class UserTokenRequest(BaseModel):
    user_id: str

class AdminTokenRequest(BaseModel):
    admin_id: str