from fastapi import APIRouter
import jwt
import datetime
from config.settings import SECRET_KEY_ADMIN, ALGORITHM
from models.generate_token_request_schema import AdminTokenRequest

router = APIRouter()

@router.post("/auth/generate-admin-token")
def generate_token(request: AdminTokenRequest):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    
    # Tambahkan role "admin" ke dalam token
    payload = {
        "user_id": request.admin_id,
        "role": "admin",  # Tambahkan role admin
        "exp": expiration
    }
    
    token = jwt.encode(payload, SECRET_KEY_ADMIN, algorithm=ALGORITHM)
    
    return {"token": token}
