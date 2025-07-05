# services/customer_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from database.models.customer_model import Customer
from schemas.customer_schema import CustomerCreate, CustomerUpdate
import logging
from fastapi import Depends
from core.config_db import config_db

logger = logging.getLogger(__name__)

class CustomerProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        try:
            return self.db.query(Customer).filter(Customer.customer_id == customer_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching customer by ID {customer_id}: {e}")
            return None

    def get_all_customers(self, limit: int = 10, offset: int = 0) -> Dict:
        """
        Mengambil semua customer dengan pagination support.

        Args:
            limit: jumlah maksimal data yang diambil
            offset: posisi awal data

        Returns:
            Dictionary berisi:
                - data: List[Customer]
                - total: int (jumlah seluruh data customer, tanpa pagination)
        """
        try:
            query = self.db.query(Customer)
            total = query.count()
            data = query.offset(offset).limit(limit).all()
            return {
                "data": data,
                "total": total
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch customers: {e}", exc_info=True)
            return {
                "data": [],
                "total": 0
            }

    def create_customer(self, payload: CustomerCreate) -> Customer:
        new_customer = Customer(**payload.dict())
        self.db.add(new_customer)
        self.db.commit()
        self.db.refresh(new_customer)
        return new_customer

    def update_customer(self, customer_id: str, payload: CustomerUpdate) -> Optional[Customer]:
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return None
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(customer, field, value)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete_customer(self, customer_id: str) -> bool:
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False
        self.db.delete(customer)
        self.db.commit()
        return True

def get_customer_service(db: Session = Depends(config_db)) -> CustomerProfileService:
    return CustomerProfileService(db)