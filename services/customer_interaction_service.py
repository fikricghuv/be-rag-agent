import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import Depends
from core.config_db import config_db
from database.models.customer_interaction_model import CustomerInteraction
from exceptions.custom_exceptions import DatabaseException
from typing import Optional


logger = logging.getLogger(__name__)

class CustomerInteractionService:
    """
    Service class untuk mengelola operasi terkait customer interaction.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all_customer_interactions(self, offset: int = 0, limit: int = 100, search: Optional[str] = None) -> dict:
        """
        Mengambil semua customer interactions dengan pagination.

        Args:
            offset (int): Data yang dilewati.
            limit (int): Jumlah maksimum data yang diambil.

        Returns:
            dict: Berisi total dan list data.
        """
        try:
            logger.info(f"[SERVICE][CUSTOMER_INTERACTION] Fetching interactions offset={offset}, limit={limit}, search='{search}'")
            query = self.db.query(CustomerInteraction)

            if search:
                search_term = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(CustomerInteraction.initial_query).ilike(search_term),
                        func.lower(CustomerInteraction.main_topic).ilike(search_term),
                        func.lower(CustomerInteraction.detected_intent).ilike(search_term),
                        func.lower(CustomerInteraction.channel).ilike(search_term),
                        func.lower(CustomerInteraction.product_involved).ilike(search_term),
                    )
                )

            total = query.count()

            interactions = (
                query.order_by(CustomerInteraction.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

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
