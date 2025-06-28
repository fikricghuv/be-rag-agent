from pydantic import BaseModel

class GenerateTokenRequest(BaseModel):
    user_id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"