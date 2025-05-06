from pydantic import BaseModel
from datetime import datetime

# Model response untuk hasil data
class UniqueNameResponse(BaseModel):
    name: str
    last_update: datetime