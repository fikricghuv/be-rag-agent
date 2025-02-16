from fastapi import APIRouter
import jwt
import datetime
from config.settings import SECRET_KEY, ALGORITHM
from models.generate_token_request_schema import UserTokenRequest

router = APIRouter()

@router.post("/auth/generate-user-token")
def generate_token(request: UserTokenRequest):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    token = jwt.encode({"user_id": request.user_id, "exp": expiration}, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"token": token}
