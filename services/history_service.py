# services/history_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc # Import desc for ordering
from database.models import Chat, RoomConversation, Member # Import necessary models
from typing import List, Dict, Any, Optional
import uuid
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class HistoryService:
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def get_user_chat_history(self, user_id: uuid.UUID, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetches chat history for a specific user's room.

        Args:
            user_id: The UUID of the user.
            limit: The maximum number of messages to retrieve.

        Returns:
            A list of dictionaries, where each dictionary represents a chat message,
            ordered by creation time. Returns an empty list if the user or room is not found.
        """
        logger.info(f"Attempting to fetch chat history for user ID: {user_id}")

        try:
            # 1. Find the room_conversation_id for the given user ID (assuming role 'user')
            #    A user should typically only have one active room.
            room_query = select(Member.room_conversation_id).where(
                Member.user_id == user_id,
                Member.role == "user"
                # Optional: Add condition for active rooms if needed, e.g., RoomConversation.status == "open"
                # .join(RoomConversation, RoomConversation.id == Member.room_conversation_id)
            ).limit(1)

            room_result = await self.db.execute(room_query)
            room_id = room_result.scalar_one_or_none()

            if not room_id:
                logger.warning(f"No active room found for user ID: {user_id}")
                return [] # Return empty list if no room is found

            logger.info(f"Found room ID {room_id} for user ID {user_id}. Fetching messages.")

            # 2. Fetch all chat messages for this room_id, ordered by created_at
            chats_query = select(Chat).where(
                Chat.room_conversation_id == room_id
            ).order_by(Chat.created_at).limit(limit) # Order by created_at as per your model

            chats_result = await self.db.execute(chats_query)
            chats = chats_result.scalars().all()

            # 3. Format the results into a list of dictionaries
            history_list = []
            for chat in chats:
                # You might want to fetch sender role or name here if needed for UI
                # For now, just include sender_id, message, and timestamp
                history_list.append({
                    "id": str(chat.id),
                    "room_conversation_id": str(chat.room_conversation_id),
                    "sender_id": str(chat.sender_id),
                    "message": chat.message,
                    "created_at": chat.created_at.isoformat() if chat.created_at else None,
                    # Include other agent metrics if the UI needs them
                    "agent_response_category": chat.agent_response_category,
                    # Note: agent_response_latency is Interval, might need conversion
                    # "agent_response_latency_seconds": chat.agent_response_latency.total_seconds() if chat.agent_response_latency else None,
                    "agent_total_tokens": chat.agent_total_tokens,
                    "agent_input_tokens": chat.agent_input_tokens,
                    "agent_output_tokens": chat.agent_output_tokens,
                    "agent_other_metrics": chat.agent_other_metrics,
                    "agent_tools_call": chat.agent_tools_call, # This is ARRAY(String)
                })

            logger.info(f"Fetched {len(history_list)} messages for room {room_id}.")
            return history_list

        except SQLAlchemyError as e:
            logger.error(f"Database error fetching chat history for user {user_id}: {e}", exc_info=True)
            # Depending on your error handling strategy, you might raise the exception
            # or return an empty list and handle the error upstream.
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching chat history for user {user_id}: {e}", exc_info=True)
            return []