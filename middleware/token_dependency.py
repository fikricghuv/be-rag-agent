# # app/dependencies/token_dependency.py
# from fastapi import Depends, status
# from jose import jwt, JWTError
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from core.settings import ALGORITHM, SECRET_KEY_ADMIN  
# from utils.exception_handler import ServiceException

# security = HTTPBearer()

# def verify_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
#     token = credentials.credentials

#     try:
#         payload = jwt.decode(token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub")
#         if not user_id:
#             raise ServiceException(code="INVALID_TOKEN",
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid token: missing user_id",
#             )
#         return user_id
#     except JWTError as e:
#         raise ServiceException(code="INVALID_TOKEN",
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token",
#         )

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from core.settings import SECRET_KEY_ADMIN, ALGORITHM
from core.config_db import config_db
from utils.exception_handler import ServiceException
from sqlalchemy import text

security = HTTPBearer()

def verify_access_token_and_get_client_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(config_db)
) -> str:
    token = credentials.credentials
    print("token yang dikirim dari ui : " + token)
    try:
        payload = jwt.decode(token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise ServiceException(code="INVALID_OR_MISSING_TOKEN",
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
            )

        print("user_id yang diterima: "+ user_id)
        
        result = db.execute(
            text("""
                SELECT client_id
                FROM ai.ms_admin_users
                WHERE id = :user_id
            """),
            {"user_id": user_id}
        ).fetchone()

        if not result:
            raise ServiceException(code="USER_ID_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
                message="User identity not found"
            )

        return str(result.client_id)

    except JWTError:
        raise ServiceException(code="INVALID_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid token",
        )

def verify_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY_ADMIN, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise ServiceException(code="INVALID_TOKEN",
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid token: missing user_id",
            )
        return user_id
    except JWTError as e:
        raise ServiceException(code="INVALID_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid token",
        )