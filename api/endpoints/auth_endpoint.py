# app/routes/auth_routes.py
from fastapi import APIRouter, Depends, Body, Path, status, HTTPException
# Mengimpor dependency API Key dan AuthService
from services.auth_service import AuthService, get_auth_service
from services.verify_api_key_header import api_key_auth
# Mengimpor model request dan respons yang sudah diperbaiki
from schemas.user_id_schema import UserIdResponse, GenerateUserIdRequest

router = APIRouter()

router = APIRouter(
    tags=["auth"], # Tag untuk dokumentasi Swagger UI
)

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