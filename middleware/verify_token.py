from fastapi import HTTPException, Request
import jwt
from core.settings import SECRET_KEY, ALGORITHM
import logging

logger = logging.getLogger(__name__)

def verify_token(request: Request):
    token = request.headers.get("Authorization")
    
    if not token:
        raise HTTPException(status_code=401, detail="Token missing.")

    if not token.startswith("Bearer "):
        logger.warning("Invalid token format.")
        raise HTTPException(status_code=401, detail="Invalid token format.")
    
    try:
        token = token.split("Bearer ")[1] 
        
        decoded_token = jwt.decode(
            token,
            SECRET_KEY, 
            algorithms=[ALGORITHM], 
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        logger.error("Token expired.")
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError as e:
        logger.error("invalid token: " + str(e))
        raise HTTPException(status_code=401, detail="Invalid token: " + str(e))