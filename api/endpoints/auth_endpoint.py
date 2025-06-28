# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, Body, Path, status, HTTPException
from services.auth_service import AuthService, get_auth_service
from middleware.verify_api_key_header import api_key_auth
from schemas.user_id_schema import UserIdResponse, GenerateUserIdRequest
from pydantic import BaseModel
from schemas.user_schema import UserResponse, CreateUserRequest
from schemas.token_schema import GenerateTokenRequest, TokenResponse
from schemas.login_schema import LoginRequest

router = APIRouter()

router = APIRouter(
    tags=["auth"], 
)

@router.post("/auth/generate_user_id", response_model=UserIdResponse, 
             status_code=status.HTTP_201_CREATED, 
             dependencies=[Depends(api_key_auth)])
async def generate_user_id_endpoint(
    request: GenerateUserIdRequest = Body(..., description="Request body with the desired role"),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Endpoint untuk menghasilkan user_id berdasarkan peran yang diterima di request body.
    Mengembalikan detail user_id yang baru dibuat.
    """
    
    user_data = auth_service.generate_user_id(role=request.role)
    
    return user_data

@router.post("/auth/generate_token", response_model=TokenResponse,
             dependencies=[Depends(api_key_auth)])
async def generate_token_endpoint(
    request: GenerateTokenRequest = Body(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint untuk menghasilkan JWT access token berdasarkan user_id.
    """
    
    token = auth_service.generate_access_token(user_id=request.user_id)
    
    return TokenResponse(access_token=token)

@router.post("/auth/login", response_model=TokenResponse)
async def login_endpoint(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login dengan email dan password, dan mendapatkan JWT access token.
    """
    token = auth_service.login_user(email=request.email, password=request.password)
    return TokenResponse(access_token=token)

@router.post("/auth/register", response_model=UserResponse)
async def register_user_endpoint(
    request: CreateUserRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint untuk register user baru dengan email dan password.
    """
    
    return auth_service.create_user(request)