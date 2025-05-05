from fastapi import APIRouter, Depends, Query
from controllers import auth_controller
from config.config_db import config_db
from sqlalchemy.orm import Session
router = APIRouter()

@router.get("/auth/generate_chat_id")
def generate_chat_id(
    role: str = Query(..., description="Role of the chat (user or admin)"),
    controller: auth_controller.AuthController = Depends(),
    db: Session = Depends(config_db)
):
    """
    Endpoint untuk menghasilkan chat_id berdasarkan peran.

    Args:
        role: Peran pengguna ('user' atau 'admin').  Diambil dari query parameter.
        controller: Instance dari AuthController yang di-inject oleh FastAPI.

    Returns:
        dict:  Chat ID yang dihasilkan.

    Raises:
        HTTPException: Jika peran tidak valid.
    """
    return {"chat_id": controller.generate_chat_id(role=role,  db=db)}