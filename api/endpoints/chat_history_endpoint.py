# app/routes/chat_history_routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path # Import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from services.chat_history_service import ChatHistoryService, get_chat_history_service # Menggunakan ChatHistoryService dan dependencynya
from middleware.verify_api_key_header import api_key_auth 
from schemas.chat_history_schema import ChatHistoryResponse, UserHistoryResponse
from uuid import UUID
from fastapi.responses import JSONResponse
from schemas.chat_history_schema import PaginatedChatHistoryResponse
from middleware.token_dependency import verify_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["history"],
)

@router.get("/history/all", response_model=PaginatedChatHistoryResponse, dependencies=[Depends(api_key_auth)])
async def read_all_chat_history_endpoint(
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    offset: int = Query(0, description="Number of items to skip"), # Default 0
    limit: int = Query(100, description="Number of items to return per page", le=200),
    access_token: str = Depends(verify_access_token) 
):
    """
    Endpoint untuk mendapatkan semua riwayat chat dengan pagination (untuk monitoring).
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        offset: Jumlah item yang akan dilewati.
        limit: Jumlah item per halaman.
    """
    try:
        
        logger.info(f"Received request for all chat history with offset={offset}, limit={limit}.")
        
        return chat_history_service.get_all_chat_history(offset=offset, limit=limit)

    except SQLAlchemyError as e:
        logger.error(f"Database error in read_all_chat_history_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching chat history."
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in read_all_chat_history_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/history/{user_id}", response_model=UserHistoryResponse, dependencies=[Depends(api_key_auth)])
async def get_user_history_by_user_id_endpoint( 
    user_id: UUID = Path(..., description="UUID of the user"), 
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    offset: int = Query(0, description="Number of items to skip"), 
    limit: int = Query(100, description="Number of items to return per page", le=200), 
    access_token: str = Depends(verify_access_token) 
):
    """
    Endpoint untuk mendapatkan riwayat chat untuk user spesifik dengan pagination.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        room_id: UUID dari user.
        offset: Jumlah item yang akan dilewati.
        limit: Jumlah item per halaman.
    """
    logger.info(f"Received request for history for user {user_id} with offset={offset}, limit={limit}.")
    try:
        result = chat_history_service.get_user_chat_history_by_user_id(user_id, offset=offset, limit=limit)
        
        logger.info(f"Returning {len(result)} history entries for room {user_id}.")

        return UserHistoryResponse(
            success=True,
            room_id=user_id,
            user_id=user_id,
            total=result["total"],
            history=[ChatHistoryResponse.model_validate(chat) for chat in result["data"]]

        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching history for room {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching room history."
        )
    
    except HTTPException as e:
         logger.warning(f"HTTPException raised fetching history for room {user_id}: {e.detail}", exc_info=True)
         raise e 
    
    except Exception as e:
        logger.error(f"Unexpected error fetching history for room {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/history/room/{room_id}", response_model=UserHistoryResponse, dependencies=[Depends(api_key_auth)])
async def get_user_history_by_room_id_endpoint( 
    room_id: UUID = Path(..., description="UUID of the user"), # Menggunakan UUID dan Path
    chat_history_service: ChatHistoryService = Depends(get_chat_history_service),
    offset: int = Query(0, description="Number of items to skip"), # Default 0
    limit: int = Query(100, description="Number of items to return per page", le=200),
    access_token: str = Depends(verify_access_token) 
):
    """
    Endpoint untuk mendapatkan riwayat chat untuk user spesifik dengan pagination.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        room_id: UUID dari user.
        offset: Jumlah item yang akan dilewati.
        limit: Jumlah item per halaman.
    """
    logger.info(f"Received request for history for user {room_id} with offset={offset}, limit={limit}.")
    try:
        result = chat_history_service.get_user_chat_history_by_room_id(room_id, offset=offset, limit=limit)

        if not result:
            return UserHistoryResponse(
                success=True,
                room_id=room_id,
                user_id=None,
                total=0,
                history=[]
            )

        user_id = result["user_id"]
        total_count = result["total_count"]
        history = result["history"]
        
        logger.info(f"Returning {len(history)} history entries for room {room_id}.")

        return UserHistoryResponse(
            success=True,
            room_id=room_id,
            user_id=user_id,
            total=total_count,
            history=[ChatHistoryResponse.model_validate(chat) for chat in history]
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching history for room {room_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching room history."
        )
    
    except HTTPException as e:
         logger.warning(f"HTTPException raised fetching history for room {room_id}: {e.detail}", exc_info=True)
         raise e 
    
    except Exception as e:
        logger.error(f"Unexpected error fetching history for room {room_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

