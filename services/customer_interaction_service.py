import logging 
from sqlalchemy.exc import SQLAlchemyError
from database.models.customer_interaction_model import CustomerInteraction
from sqlalchemy.orm import Session
from fastapi import Depends
from core.config_db import config_db 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomerInteractionService:
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


    def get_all_customer_interactions(self, offset: int = 0, limit: int = 100) -> dict:
        try:
            total = self.db.query(CustomerInteraction).count()

            interactions = self.db.query(CustomerInteraction) \
                .order_by(CustomerInteraction.created_at.desc()) \
                .offset(offset).limit(limit).all()

            return {
                "total": total,
                "data": interactions
            }

        except SQLAlchemyError as e:
            logger.error("Database error on get_all_customer_interactions: %s", str(e))
            raise

def get_customer_interaction_service(db: Session = Depends(config_db)):
    """
    Dependency untuk mendapatkan instance CustomerInteractionService dengan sesi database.
    """
    return CustomerInteractionService(db)