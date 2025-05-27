# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, Body, Path, status, HTTPException
from services.auth_service import AuthService, get_auth_service
from services.verify_api_key_header import api_key_auth
from schemas.user_id_schema import UserIdResponse, GenerateUserIdRequest
from pydantic import BaseModel
from schemas.user_schema import UserResponse, CreateUserRequest

router = APIRouter()

router = APIRouter(
    tags=["auth"], # Tag untuk dokumentasi Swagger UI
)

class GenerateTokenRequest(BaseModel):
    user_id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Menggunakan request body dan model GenerateUserIdRequest
@router.post("/auth/generate_user_id", response_model=UserIdResponse, 
             status_code=status.HTTP_201_CREATED, 
             dependencies=[Depends(api_key_auth)])
async def generate_user_id_endpoint(
    # Menggunakan Body untuk menerima data dari request body
    request: GenerateUserIdRequest = Body(..., description="Request body with the desired role"),
    auth_service: AuthService = Depends(get_auth_service),
    # Tambahkan dependency api_key_auth jika endpoint ini juga perlu diamankan
):
    """
    Endpoint untuk menghasilkan user_id berdasarkan peran yang diterima di request body.
    Mengembalikan detail user_id yang baru dibuat.
    """
    # Role sudah divalidasi oleh Pydantic model GenerateUserIdRequest menggunakan Enum UserRole
    # Memanggil service method dengan nilai Enum role
    user_data = auth_service.generate_user_id(role=request.role)
    # Service method sudah mengembalikan UserIdResponse, tinggal dikembalikan
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

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/auth/login", response_model=TokenResponse)
async def login_endpoint(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
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