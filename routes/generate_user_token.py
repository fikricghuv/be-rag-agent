from fastapi import APIRouter
from sqlalchemy.orm import Session
from config.config_db import config_db
from models.generate_token_request_schema import UserTokenRequest, UserRefreshTokenRequest
from controllers.auth_controller import generate_user_token, refresh_user_token

router = APIRouter()

@router.post("/auth/generate-user-token")
def generate_token(request: UserTokenRequest):
    return generate_user_token(request)

@router.post("/auth/refresh-user-token")
def refresh_token_user(request: UserRefreshTokenRequest):
    return refresh_user_token(request)
