import logging
from fastapi import APIRouter, Depends, Query, Path
from typing import List, Optional
from uuid import UUID
from services.chat_history_service import ChatHistoryService, get_chat_history_service
from middleware.token_dependency import verify_access_token_and_get_client_id
from schemas.chat_history_schema import ChatHistoryResponse, UserHistoryResponse, PaginatedChatHistoryResponse, UserHistoryByIdResponse
from utils.exception_handler import handle_exceptions
from middleware.auth_client_dependency import get_authenticated_client
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["history"])

@router.get("/history/all", response_model=PaginatedChatHistoryResponse)
@handle_exceptions(tag="[HISTORY][ALL]")
async def read_all_chat_history_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    offset: int = Query(0),
    limit: int = Query(100, le=200),
    search: Optional[str] = Query(None, description="Filter chat by message or sender_id"),
    client_id: UUID = Depends(verify_access_token_and_get_client_id)
):
    logger.info(f"[HISTORY][ALL] Fetching all chat history with offset={offset}, limit={limit}, search={search}")
    return chat_history_service.get_all_chat_history(offset=offset, limit=limit, search=search, client_id=client_id)

@router.get("/history/{user_id}", response_model=UserHistoryByIdResponse)
@handle_exceptions(tag="[HISTORY][USER_ID]")
async def get_user_history_by_user_id_endpoint( 
    user_id: UUID = Path(..., description="UUID of the user"), 
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    cursor: Optional[datetime] = Query(None, description="Cursor berupa timestamp terakhir (created_at)"),
    limit: int = Query(15, le=200),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[HISTORY][USER_ID] Fetching chat history for user_id={user_id}, cursor={cursor}, limit={limit}")
    result = chat_history_service.get_user_chat_history_by_user_id(
        user_id, cursor=cursor, limit=limit, client_id=client_id
    )

    if not result or len(result["history"]) == 0:
        logger.info(f"[HISTORY][USER_ID] No chat history found for user_id={user_id}")
        return UserHistoryByIdResponse(
            success=True,
            room_id=None, 
            user_id=user_id,
            total=0,
            history=[],
            next_cursor=None
        )

    logger.info(f"[HISTORY][USER_ID] Found {result['total_count']} messages for user_id={user_id}")
    return UserHistoryByIdResponse(
        success=True,
        room_id=None,
        user_id=user_id,
        total=result["total_count"],
        history=[ChatHistoryResponse.model_validate(chat) for chat in result["history"]],
        next_cursor=result["next_cursor"]
    )

@router.get("/history/room/{room_id}", response_model=UserHistoryResponse)
@handle_exceptions(tag="[HISTORY][ROOM_ID]")
async def get_user_history_by_room_id_endpoint(
    room_id: UUID = Path(..., description="UUID of the room"), 
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    cursor: Optional[datetime] = Query(None, description="Cursor berupa timestamp terakhir (created_at)"),
    limit: int = Query(50, le=200),
    client_id: UUID = Depends(verify_access_token_and_get_client_id) 
):
    logger.info(f"[HISTORY][ROOM_ID] Fetching chat history for room_id={room_id}, cursor={cursor}, limit={limit}")
    result = chat_history_service.get_user_chat_history_by_room_id(
        room_id, cursor=cursor, limit=limit, client_id=client_id
    )

    if not result or len(result["history"]) == 0:
        logger.info(f"[HISTORY][ROOM_ID] No chat history found for room_id={room_id}")
        return UserHistoryResponse(
            success=True,
            room_id=room_id,
            user_id=None,
            total=0,
            history=[],
            next_cursor=None
        )

    logger.info(f"[HISTORY][ROOM_ID] Found {result['total_count']} messages for room_id={room_id}")
    return UserHistoryResponse(
        success=True,
        room_id=room_id,
        user_id=result["user_id"],
        total=result["total_count"],
        history=[ChatHistoryResponse.model_validate(chat) for chat in result["history"]],
        next_cursor=result["next_cursor"]
    )
