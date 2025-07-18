from uuid import UUID
from fastapi import APIRouter, Depends, Query, Body
from services.notification_service import NotificationService, get_notification_service
from middleware.token_dependency import verify_access_token
from utils.exception_handler import handle_exceptions
from middleware.verify_api_key_header import api_key_auth
from schemas.notification_schema import NotificationListResponse, NotificationItem
import logging

router = APIRouter(tags=["notifications"])
logger = logging.getLogger(__name__)

@router.get("/notifications", response_model=NotificationListResponse, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[NOTIFICATION]")
async def get_notifications_endpoint(
    limit: int = Query(20),
    offset: int = Query(0),
    current_user: str = Depends(verify_access_token),
    notification_service: NotificationService = Depends(get_notification_service),
):
    user_id = UUID(current_user)
    logger.info(f"[NOTIFICATION] Getting notifications for user_id={user_id}")

    notifs, total = await notification_service.get_notifications(user_id, limit, offset)

    notifs_response = [NotificationItem.model_validate(n) for n in notifs]

    return NotificationListResponse(
        success=True,
        total=total,
        data=notifs_response
    )

@router.patch("/notifications/{notification_id}/read")
@handle_exceptions(tag="[NOTIFICATION]")
async def mark_as_read(
    notification_id: UUID,
    # receiver_id: UUID,  
    notification_service: NotificationService = Depends(get_notification_service),
    receiver_id: str = Depends(verify_access_token)
):
    user_id = UUID(receiver_id)
    return await notification_service.mark_notification_as_read(notification_id, user_id)

@router.patch("/notifications/clear")
@handle_exceptions(tag="[NOTIFICATION]")
async def clear_notifications(
    # receiver_id: UUID = Query(...),
    notification_service: NotificationService = Depends(get_notification_service),
    receiver_id: str = Depends(verify_access_token)
):
    user_id = UUID(receiver_id)
    return await notification_service.soft_delete_all_by_receiver(user_id)

