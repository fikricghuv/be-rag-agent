from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    user_id: str