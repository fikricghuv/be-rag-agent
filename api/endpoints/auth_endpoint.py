from fastapi import APIRouter, Depends, Query
from services.auth_service import AuthService, get_auth_service
from models.chat_id_model import ChatIdResponse

router = APIRouter()

@router.get("/auth/generate_chat_id", response_model=ChatIdResponse)
async def generate_chat_id_endpoint(
    role: str = Query(..., description="Role of the chat (user or admin)"),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Endpoint untuk menghasilkan chat_id berdasarkan peran.
    """
    chat_id = auth_service.generate_chat_id(role=role)
    return ChatIdResponse(chat_id=chat_id)