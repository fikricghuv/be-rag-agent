from pydantic import BaseModel

class AdminMessageRequest(BaseModel):
    user_id: str
    message: str