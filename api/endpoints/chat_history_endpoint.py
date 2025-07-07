import logging
from fastapi import APIRouter, Depends, Query, Path
from typing import List, Optional
from uuid import UUID
from services.chat_history_service import ChatHistoryService, get_chat_history_service
from middleware.verify_api_key_header import api_key_auth
from middleware.token_dependency import verify_access_token
from schemas.chat_history_schema import ChatHistoryResponse, UserHistoryResponse, PaginatedChatHistoryResponse
from utils.exception_handler import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["history"])

@router.get("/history/all", response_model=PaginatedChatHistoryResponse, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[HISTORY][ALL]")
async def read_all_chat_history_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    offset: int = Query(0),
    limit: int = Query(100, le=200),
    search: Optional[str] = Query(None, description="Filter chat by message or sender_id"),
    access_token: str = Depends(verify_access_token)
):
    logger.info(f"[HISTORY][ALL] Fetching all chat history with offset={offset}, limit={limit}, search={search}")
    return chat_history_service.get_all_chat_history(offset=offset, limit=limit, search=search)

@router.get("/history/{user_id}", response_model=UserHistoryResponse, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[HISTORY][USER_ID]")
async def get_user_history_by_user_id_endpoint( 
    user_id: UUID = Path(..., description="UUID of the user"), 
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    offset: int = Query(0), 
    limit: int = Query(100, le=200),
):
    logger.info(f"[HISTORY][USER_ID] Fetching chat history for user_id={user_id}, offset={offset}, limit={limit}")
    result = chat_history_service.get_user_chat_history_by_user_id(user_id, offset=offset, limit=limit)

    return UserHistoryResponse(
        success=True,
        room_id=user_id,
        user_id=user_id,
        total=result["total"],
        history=[ChatHistoryResponse.model_validate(chat) for chat in result["data"]]
    )

@router.get("/history/room/{room_id}", response_model=UserHistoryResponse, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[HISTORY][ROOM_ID]")
async def get_user_history_by_room_id_endpoint( 
    room_id: UUID = Path(..., description="UUID of the room"), 
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    offset: int = Query(0),
    limit: int = Query(100, le=200),
    access_token: str = Depends(verify_access_token) 
):
    logger.info(f"[HISTORY][ROOM_ID] Fetching chat history for room_id={room_id}, offset={offset}, limit={limit}")
    result = chat_history_service.get_user_chat_history_by_room_id(room_id, offset=offset, limit=limit)

    if not result:
        logger.info(f"[HISTORY][ROOM_ID] No chat history found for room_id={room_id}")
        return UserHistoryResponse(
            success=True,
            room_id=room_id,
            user_id=None,
            total=0,
            history=[]
        )

    logger.info(f"[HISTORY][ROOM_ID] Found {result['total_count']} messages for room_id={room_id}")
    return UserHistoryResponse(
        success=True,
        room_id=room_id,
        user_id=result["user_id"],
        total=result["total_count"],
        history=[ChatHistoryResponse.model_validate(chat) for chat in result["history"]]
    )
