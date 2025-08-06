import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from sqlalchemy import or_, func
from fastapi import Depends
from core.config_db import config_db
from database.models.customer_model import Customer
from schemas.customer_schema import CustomerCreate, CustomerUpdate
from exceptions.custom_exceptions import DatabaseException
from uuid import UUID

logger = logging.getLogger(__name__)

class CustomerProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_customer_by_id(self, customer_id: str, client_id: UUID) -> Optional[Customer]:
        try:
            logger.info(f"[SERVICE][CUSTOMER] Fetching customer by ID: {customer_id} for client {client_id}")
            return (
                self.db.query(Customer)
                .filter(
                    Customer.customer_id == customer_id,
                    Customer.client_id == client_id
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][CUSTOMER] DB error fetching customer by ID {customer_id}: {e}", exc_info=True)
            raise DatabaseException(code="DB_GET_CUSTOMER_BY_ID_ERROR", message="Failed to fetch customer by ID.")


    def get_all_customers(self, client_id: UUID, limit: int = 10, offset: int = 0, search: Optional[str] = None) -> Dict:
        try:
            logger.info(f"[SERVICE][CUSTOMER] Fetching all customers for client {client_id}: offset={offset}, limit={limit}, search='{search}'")
            query = self.db.query(Customer).filter(Customer.client_id == client_id)

            if search:
                search_term = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(Customer.full_name).ilike(search_term),
                        func.lower(Customer.email).ilike(search_term),
                        func.lower(Customer.phone_number).ilike(search_term)
                    )
                )

            total = query.count()
            data = query.offset(offset).limit(limit).all()

            logger.info(f"[SERVICE][CUSTOMER] Found {len(data)} customer(s) for client {client_id}")

            return {
                "data": data,
                "total": total
            }

        except SQLAlchemyError as e:
            logger.error("[SERVICE][CUSTOMER] DB error fetching all customers: %s", e, exc_info=True)
            raise DatabaseException(code="DB_GET_ALL_CUSTOMERS_ERROR", message="Failed to fetch all customers.")


    def create_customer(self, payload: CustomerCreate, client_id: UUID) -> Customer:
        try:
            logger.info(f"[SERVICE][CUSTOMER] Creating new customer for client {client_id}: {payload.email}")
            new_customer = Customer(**payload.dict(), client_id=client_id)
            self.db.add(new_customer)
            self.db.commit()
            self.db.refresh(new_customer)
            return new_customer
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][CUSTOMER] DB error creating customer: {e}", exc_info=True)
            raise DatabaseException(code="DB_CREATE_CUSTOMER_ERROR", message="Failed to create new customer.")


    def update_customer(self, customer_id: str, client_id: UUID, payload: CustomerUpdate) -> Optional[Customer]:
        try:
            logger.info(f"[SERVICE][CUSTOMER] Updating customer {customer_id} for client {client_id}")
            customer = self.get_customer_by_id(customer_id, client_id)
            if not customer:
                logger.warning(f"[SERVICE][CUSTOMER] Customer not found: {customer_id} for client {client_id}")
                return None

            for field, value in payload.dict(exclude_unset=True).items():
                setattr(customer, field, value)

            self.db.commit()
            self.db.refresh(customer)
            return customer
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][CUSTOMER] DB error updating customer {customer_id}: {e}", exc_info=True)
            raise DatabaseException(code="DB_UPDATE_CUSTOMER_ERROR", message="Failed to update customer.")


    def delete_customer(self, customer_id: str, client_id: UUID) -> bool:
        try:
            logger.info(f"[SERVICE][CUSTOMER] Deleting customer {customer_id} for client {client_id}")
            customer = self.get_customer_by_id(customer_id, client_id)
            if not customer:
                logger.warning(f"[SERVICE][CUSTOMER] Customer not found for delete: {customer_id} client {client_id}")
                return False

            self.db.delete(customer)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"[SERVICE][CUSTOMER] DB error deleting customer {customer_id}: {e}", exc_info=True)
            raise DatabaseException(code="DB_DELETE_CUSTOMER_ERROR", message="Failed to delete customer.")

def get_customer_service(db: Session = Depends(config_db)) -> CustomerProfileService:
    return CustomerProfileService(db)
