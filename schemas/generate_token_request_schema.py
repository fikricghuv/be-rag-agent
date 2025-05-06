from pydantic import BaseModel

class UserTokenRequest(BaseModel):
    user_id: str

class UserRefreshTokenRequest(BaseModel):
    refresh_token: str

class AdminTokenRequest(BaseModel):
    admin_id: str

class AdminRefreshTokenRequest(BaseModel):
    refresh_token_admin: str