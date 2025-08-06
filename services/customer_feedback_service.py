import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from database.models.customer_feedback_model import CustomerFeedback
from fastapi import Depends
from core.config_db import config_db
from exceptions.custom_exceptions import DatabaseException
from uuid import UUID
logger = logging.getLogger(__name__)

class CustomerFeedbackService:
    """
    Service class untuk mengelola operasi terkait customer feedback.
    """
    def __init__(self, db: Session):
        self.db = db

    def fetch_all_feedbacks(self, offset: int, limit: int, client_id: UUID, search: Optional[str] = None) -> List[CustomerFeedback]:
        try:
            logger.info(f"[SERVICE][CUSTOMER_FEEDBACK] Fetching feedbacks for client_id={client_id}, offset={offset}, limit={limit}, search='{search}'")
            
            query = self.db.query(CustomerFeedback).filter(CustomerFeedback.client_id == client_id)

            if search:
                search_filter = f"%{search.lower()}%"
                query = query.filter(func.lower(CustomerFeedback.feedback_from_customer).like(search_filter))

            feedbacks = (
                query.order_by(desc(CustomerFeedback.created_at))
                    .offset(offset)
                    .limit(limit)
                    .all()
            )

            logger.info(f"[SERVICE][CUSTOMER_FEEDBACK] Retrieved {len(feedbacks)} feedback(s) for client_id={client_id}")
            return feedbacks

        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][CUSTOMER_FEEDBACK] DB error while fetching feedbacks: {e}", exc_info=True)
            raise DatabaseException(code="DB_FETCH_ERROR", message="Failed to fetch feedbacks from database.")


    def count_total_feedbacks(self, client_id: UUID) -> int:
        """
        Menghitung total jumlah feedback di database berdasarkan client_id.
        """
        try:
            logger.info(f"[SERVICE][CUSTOMER_FEEDBACK] Counting total feedbacks for client_id={client_id}")
            total_count = (
                self.db.query(func.count(CustomerFeedback.id))
                .filter(CustomerFeedback.client_id == client_id)
                .scalar()
            )
            logger.info(f"[SERVICE][CUSTOMER_FEEDBACK] Total feedbacks for client_id={client_id}: {total_count}")
            return total_count

        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][CUSTOMER_FEEDBACK] DB error while counting feedbacks: {e}", exc_info=True)
            raise DatabaseException(code="DB_COUNT_ERROR", message="Failed to count feedbacks.")

def get_customer_feedback_service(db: Session = Depends(config_db)):
    return CustomerFeedbackService(db)
