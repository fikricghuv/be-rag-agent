from pydantic import BaseModel

class PromptUpdate(BaseModel):
    content: str