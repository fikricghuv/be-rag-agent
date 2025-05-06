from pydantic import BaseModel

class TotalUniqueUsersResponse(BaseModel):
    total_users: int