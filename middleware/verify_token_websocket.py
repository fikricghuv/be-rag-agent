from config.settings import SECRET_KEY, ALGORITHM, SECRET_KEY_ADMIN
from fastapi import HTTPException
import jwt

def verify_token(token: str):
    """Coba decode token dengan dua SECRET_KEY"""
    for key in [SECRET_KEY, SECRET_KEY_ADMIN]:
        try:
            return jwt.decode(token, key, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidSignatureError:
            continue  # Coba SECRET_KEY yang lain
    raise HTTPException(status_code=401, detail="Invalid token")