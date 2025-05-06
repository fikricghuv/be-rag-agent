from pydantic import BaseModel

class ChatIdResponse(BaseModel):
    chat_id: str