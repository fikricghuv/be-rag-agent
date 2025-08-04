from sqlalchemy.orm import Session
from database.models.chat_model import Chat
from database.models.customer_model import Customer 
from agents.analysis_chat_agent.analysis_chat_agent import analysis_chat
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime, time

logger = logging.getLogger(__name__)

import json
import re

def clean_json_string(json_str: str) -> str:
    """Hapus wrapping markdown seperti ```json ... ``` dan whitespace."""
    return re.sub(r"^```json|```$", "", json_str.strip(), flags=re.MULTILINE).strip()

def process_user_chats(db: Session):
    try:
        chats = db.query(Chat).filter(
            Chat.role == 'user',
            Chat.message.isnot(None),
            Chat.created_at >= datetime.utcnow().date()  
        ).all()

        logger.info(f"Processing {len(chats)} user chat messages...")

        for chat in chats:
            try:
                raw_result = analysis_chat(chat.message)

                if isinstance(raw_result, str):
                    cleaned = clean_json_string(raw_result)
                    result = json.loads(cleaned)
                else:
                    result = raw_result

                # Cek apakah customer dengan conversation_id = chat.id sudah ada
                logger.info(f"perbandingan cusomer.sender_id == chat.sender_id {Customer.sender_id} {chat.sender_id}" )
                existing_customer = db.query(Customer).filter(Customer.sender_id == chat.sender_id).first()

                if existing_customer:
                    # Update data yang sudah ada
                    existing_customer.sender_id = chat.sender_id
                    existing_customer.full_name = result.get("full_name")
                    existing_customer.email = result.get("email")
                    existing_customer.phone_number = result.get("phone")
                    existing_customer.address = result.get("address")
                    existing_customer.other_info = result.get("other_info")
                    existing_customer.source_message = chat.message
                    existing_customer.last_activity_at = chat.created_at
                    logger.info(f"Updated existing customer for sender ID {chat.sender_id}")
                else:
                    # Tambahkan data baru
                    customer_data = Customer(
                        conversation_id=chat.id,
                        sender_id=chat.sender_id,
                        full_name=result.get("full_name"),
                        email=result.get("email"),
                        phone_number=result.get("phone"),
                        address=result.get("address"),
                        other_info=result.get("other_info"),
                        source_message=chat.message,
                        last_activity_at=chat.created_at
                    )
                    db.add(customer_data)
                    logger.info(f"Inserted new customer for sender ID {chat.sender_id}")

            except Exception as e:
                logger.error(f"Failed to analyze chat ID {chat.id}: {e}", exc_info=True)
                continue

        db.commit()
        logger.info("User chat analysis and CRM extraction completed successfully.")

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during processing user chats: {e}", exc_info=True)
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during processing user chats: {e}", exc_info=True)
