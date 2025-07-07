import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi import Depends
from core.config_db import config_db
from database.models.customer_interaction_model import CustomerInteraction
from exceptions.custom_exceptions import DatabaseException

logger = logging.getLogger(__name__)

class CustomerInteractionService:
    """
    Service class untuk mengelola operasi terkait customer interaction.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all_customer_interactions(self, offset: int = 0, limit: int = 100) -> dict:
        """
        Mengambil semua customer interactions dengan pagination.

        Args:
            offset (int): Data yang dilewati.
            limit (int): Jumlah maksimum data yang diambil.

        Returns:
            dict: Berisi total dan list data.
        """
        try:
            logger.info(f"[SERVICE][CUSTOMER_INTERACTION] Fetching interactions offset={offset}, limit={limit}")

            total = self.db.query(CustomerInteraction).count()

            interactions = self.db.query(CustomerInteraction) \
                .order_by(CustomerInteraction.created_at.desc()) \
                .offset(offset).limit(limit).all()

            logger.info(f"[SERVICE][CUSTOMER_INTERACTION] Retrieved {len(interactions)} interaction(s).")

            return {
                "total": total,
                "data": interactions
            }

        except SQLAlchemyError as e:
            logger.error("[SERVICE][CUSTOMER_INTERACTION] DB error: %s", str(e), exc_info=True)
            raise DatabaseException(code="DB_FETCH_ERROR", message="Failed to fetch customer interactions from database.")

def get_customer_interaction_service(db: Session = Depends(config_db)):
    return CustomerInteractionService(db)
