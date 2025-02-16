from fastapi import APIRouter
import jwt
import datetime
from config.settings import SECRET_KEY_ADMIN, ALGORITHM
from models.generate_token_request_schema import AdminTokenRequest

router = APIRouter()

@router.post("/auth/generate-admin-token")
def generate_token(request: AdminTokenRequest):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    token = jwt.encode({"admin_id": request.admin_id, "exp": expiration}, SECRET_KEY_ADMIN, algorithm=ALGORITHM)
    
    return {"token": token}
