from pydantic import BaseModel

class PromptResponse(BaseModel):
    name: str
    content: str

class PromptUpdate(BaseModel):
    content: str