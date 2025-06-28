import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from core.settings import SECRET_KEY_ADMIN, SECRET_KEY_REFRESH_ADMIN, ALGORITHM

# Simpan sementara refresh tokens
refresh_tokens = {}

def _create_token(data: dict, secret_key: str, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)

def create_access_token(admin_id: str, role: str = "admin", expires_delta: timedelta = timedelta(minutes=15)):
    return _create_token({
        "sub": admin_id, 
        "role": role
        }, SECRET_KEY_ADMIN, expires_delta)

def create_refresh_token(admin_id: str, expires_delta: timedelta = timedelta(days=7)):
    return _create_token({
        "sub": admin_id, 
        "type": "refresh"}, SECRET_KEY_REFRESH_ADMIN, expires_delta)

def decode_refresh_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY_REFRESH_ADMIN, algorithms=[ALGORITHM])
        admin_id = payload.get("sub")
        token_type = payload.get("type")

        if not admin_id or token_type != "refresh":
            raise HTTPException(status_code=400, detail="Invalid refresh token")

        return admin_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

def store_refresh_token(token: str, admin_id: str):
    refresh_tokens[token] = admin_id

def validate_refresh_token(token: str, admin_id: str) -> bool:
    return token in refresh_tokens and refresh_tokens[token] == admin_id
