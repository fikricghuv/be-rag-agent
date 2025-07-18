from pydantic import BaseModel

class FCMRequest(BaseModel):
    token: str
    title: str
    body: str

class FCMTokenRequest(BaseModel):
    token: str
