from fastapi import APIRouter
import jwt
import datetime
from config.settings import SECRET_KEY
from models.generate_token_request_schema import TokenRequest

router = APIRouter()

@router.post("/auth/generate-token")
def generate_token(request: TokenRequest):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    token = jwt.encode({"user_id": request.user_id, "exp": expiration}, SECRET_KEY, algorithm="HS256")
    print("generate token: " + token)
    return {"token": token}
