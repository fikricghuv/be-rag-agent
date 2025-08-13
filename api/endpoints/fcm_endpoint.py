from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from services.fcm_service import FCMService
from schemas.fcm_schema import FCMTokenRequest, FCMRequest
from core.config_db import get_db
from database.models.user_model import User
from middleware.get_current_user import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from middleware.token_dependency import verify_access_token_and_get_client_id

router = APIRouter()

@router.post("/send-notification")
async def send_fcm(
    request: FCMRequest,
    db: AsyncSession = Depends(get_db)  
):
    fcm = FCMService(db) 
    response = await fcm.send_message(
        fcm_token=request.token,
        title=request.title,
        body=request.body
    )
    return {"status": "success", "fcm_response": response}


@router.post("/fcm-token")
async def register_fcm_token(
    data: FCMTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    fcm = FCMService(db)
    await fcm.save_fcm_token(db=db, user_id=UUID(str(current_user.id)), token=data.token, client_id=client_id) 
    return {"success": True, "message": "FCM token disimpan"}
