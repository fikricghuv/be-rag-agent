# app/api/endpoints/room_routes.py
import logging
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from services.room_service import RoomService, get_room_service
from middleware.token_dependency import verify_access_token
from schemas.room_conversation_schema import RoomConversationResponse
from utils.exception_handler import handle_exceptions 
from middleware.auth_client_dependency import get_authenticated_client
from uuid import UUID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["rooms"])

@router.get("/rooms/get-all-rooms", response_model=List[RoomConversationResponse])
@handle_exceptions(tag="[ROOM]")
async def get_all_rooms_endpoint(
    room_service: RoomService = Depends(get_room_service),
    offset: int = Query(0, description="Number of items to skip"), 
    limit: int = Query(100, description="Number of items to return per page", le=200), 
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client) 
):
    logger.info(f"[ROOM] get_all_rooms: offset={offset}, limit={limit}")
    return room_service.get_all_rooms(offset=offset, limit=limit, client_id=client_id)

@router.get("/rooms/active-rooms", response_model=List[RoomConversationResponse])
@handle_exceptions(tag="[ROOM]")
async def get_active_rooms_endpoint(
    room_service: RoomService = Depends(get_room_service),
    offset: int = Query(0, description="Number of active items to skip"),
    limit: int = Query(100, description="Number of active items to return per page", le=200),
    search: Optional[str] = Query(None, description="Search keyword for room ID, name, or message"),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client) 
):
    logger.info(f"[ROOM] get_active_rooms: offset={offset}, limit={limit}, search={search}")
    return room_service.get_active_rooms(offset=offset, limit=limit, search=search, client_id=client_id)
