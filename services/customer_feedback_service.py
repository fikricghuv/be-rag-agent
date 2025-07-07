# app/services/customer_feedback_service.py
import logging # Import logging
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc 
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from database.models.customer_feedback_model import CustomerFeedback
from fastapi import Depends

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomerFeedbackService:
    """
    Service class untuk mengelola operasi terkait customer feedback.
    """
    def __init__(self, db: Session):
        """
        Inisialisasi CustomerFeedbackService dengan sesi database.

        Args:
            db: SQLAlchemy Session object.
        """
        self.db = db

    def fetch_all_feedbacks(self, offset: int, limit: int, search: Optional[str] = None) -> List[CustomerFeedback]:
        try:
            logger.info(f"Fetching customer feedbacks with offset={offset}, limit={limit}, search='{search}'")
            query = self.db.query(CustomerFeedback)

            if search:
                search_filter = f"%{search.lower()}%"
                query = query.filter(func.lower(CustomerFeedback.feedback_from_customer).like(search_filter))

            feedbacks = query.order_by(desc(CustomerFeedback.created_at))\
                            .offset(offset)\
                            .limit(limit)\
                            .all()

            return feedbacks
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error fetching customer feedbacks: {e}", exc_info=True)
            raise e


    def count_total_feedbacks(self) -> int:
        """
        Menghitung total jumlah feedback di database.

        Returns:
            Total jumlah feedback sebagai integer.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info("Counting total customer feedbacks.")
            
            total_count = self.db.query(func.count(CustomerFeedback.id)).scalar()
            logger.info(f"Total customer feedbacks found: {total_count}.")
            
            return total_count
        
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy Error counting total customer feedbacks: {e}", exc_info=True)
            raise e

from core.config_db import config_db 

def get_customer_feedback_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance CustomerFeedbackService dengan sesi database.
    """
    return CustomerFeedbackService(db)

