# app/services/customer_feedback_service.py
import logging # Import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from typing import List
# Asumsi model CustomerFeedback diimpor dari database.models.customer_feedback_model
from database.models.customer_feedback_model import CustomerFeedback
from fastapi import Depends

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
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

    # Mengubah menjadi instance method dan menambahkan parameter pagination
    def fetch_all_feedbacks(self, offset: int = 0, limit: int = 100) -> List[CustomerFeedback]:
        """
        Mengambil data feedback dari database dengan pagination.

        Args:
            offset: Jumlah item yang akan dilewati.
            limit: Jumlah item per halaman.

        Returns:
            List of CustomerFeedback objects.
        Raises:
            SQLAlchemyError: Jika terjadi kesalahan saat berinteraksi dengan database.
        """
        try:
            logger.info(f"Fetching customer feedbacks with offset={offset}, limit={limit}.")
            # Menggunakan self.db dan menerapkan pagination
            feedbacks = self.db.query(CustomerFeedback)\
                .offset(offset)\
                .limit(limit)\
                .all() # Menggunakan .all() setelah limit/offset
            logger.info(f"Successfully fetched {len(feedbacks)} feedback entries.")
            return feedbacks
        except SQLAlchemyError as e:
            # Log error detail di sini, tapi biarkan exception propagate
            logger.error(f"SQLAlchemy Error fetching customer feedbacks: {e}", exc_info=True)
            raise e # Re-raise SQLAlchemyError

    # Anda bisa menambahkan metode service lain di sini jika diperlukan
    # Contoh: get_feedback_by_id, create_feedback, update_feedback, delete_feedback

# Dependency function untuk menyediakan instance CustomerFeedbackService
from core.config_db import config_db # Pastikan ini diimpor dengan benar

def get_customer_feedback_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance CustomerFeedbackService dengan sesi database.
    """
    return CustomerFeedbackService(db)

