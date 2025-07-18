import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path, status
from middleware.verify_api_key_header import api_key_auth
from middleware.token_dependency import verify_access_token
from schemas.user_activity_log_schema import UserActivityLogResponse
from services.user_activity_log_service import UserActivityLogService, get_user_activity_log_service
from utils.exception_handler import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["user-activity-log"])

@router.get("/user-activity-logs", response_model=List[UserActivityLogResponse], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[USER_ACTIVITY_LOG]")
async def get_user_activity_logs(
    offset: int = Query(0, ge=0, description="Jumlah data yang dilewati"),
    limit: int = Query(10, le=20, description="Jumlah data yang diambil"),
    search: Optional[str] = Query(None, description="Kata kunci pencarian"),
    log_service: UserActivityLogService = Depends(get_user_activity_log_service),
    access_token: str = Depends(verify_access_token)
):
    logger.info(f"[USER_ACTIVITY_LOG] Requesting logs (offset={offset}, limit={limit}, search={search})")
    return log_service.get_all_logs(offset=offset, limit=limit, search=search)

@router.get("/activity-logs/{user_id}", response_model=List[UserActivityLogResponse], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[ACTIVITY_LOG]")
async def get_activity_logs_by_user_id(
    user_id: UUID = Path(..., description="ID pengguna"),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
    activity_service: UserActivityLogService = Depends(get_user_activity_log_service),
    token: str = Depends(verify_access_token)
):
    return activity_service.get_logs_by_user_id(user_id=user_id, offset=offset, limit=limit)