# app/dependencies/token_dependency.py
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.settings import SECRET_KEY_REFRESH_ADMIN, ALGORITHM, SECRET_KEY_ADMIN  # gunakan secret untuk access token

security = HTTPBearer()

def verify_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
            )
        return user_id
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
