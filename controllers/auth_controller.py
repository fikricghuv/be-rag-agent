from fastapi import HTTPException
from models.generate_token_request_schema import UserTokenRequest, UserRefreshTokenRequest
from utils.token_utils import create_access_token, create_refresh_token, decode_refresh_token

def generate_user_token(request: UserTokenRequest):
    access_token = create_access_token(request.user_id)
    refresh_token = create_refresh_token(request.user_id)
    
    return {
        "role": "user",
        "token": access_token,
        "refresh_token": refresh_token
    }

def refresh_user_token(request: UserRefreshTokenRequest):
    user_id = decode_refresh_token(request.refresh_token)

    new_access_token = create_access_token(user_id)
    return {"token": new_access_token}
