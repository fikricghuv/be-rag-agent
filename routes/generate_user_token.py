from fastapi import APIRouter, HTTPException
import jwt
from datetime import datetime, timedelta
from config.settings import SECRET_KEY, ALGORITHM, SECRET_KEY_REFRESH_USER
from models.generate_token_request_schema import UserTokenRequest, UserRefreshTokenRequest

router = APIRouter()

def create_access_token(user_id: str, role: str = "user", expires_delta: timedelta = timedelta(minutes=15)) -> str:
    to_encode = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str, expires_delta: timedelta = timedelta(days=7)) -> str:
    to_encode = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(to_encode, SECRET_KEY_REFRESH_USER, algorithm=ALGORITHM)

@router.post("/auth/generate-user-token")
def generate_token(request: UserTokenRequest):
    access_token = create_access_token(request.user_id)
    refresh_token = create_refresh_token(request.user_id)
    
    return {
        "role": "user",
        "token": access_token,
        "refresh_token": refresh_token
    }

@router.post("/auth/refresh-user-token")
def refresh_token_user(request: UserRefreshTokenRequest):
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY_REFRESH_USER, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "refresh":
            raise HTTPException(status_code=400, detail="Invalid refresh token")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(user_id)
    return {"token": new_access_token}
