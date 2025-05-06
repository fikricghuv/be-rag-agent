import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from core.settings import SECRET_KEY, ALGORITHM, SECRET_KEY_REFRESH_USER

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

def decode_refresh_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY_REFRESH_USER, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "refresh":
            raise HTTPException(status_code=400, detail="Invalid refresh token")

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
