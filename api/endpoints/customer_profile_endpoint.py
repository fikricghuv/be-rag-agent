# routers/customer_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from schemas.customer_schema import CustomerOut, CustomerResponse
from services.customer_profile import CustomerProfileService, get_customer_service
from middleware.token_dependency import verify_access_token

router = APIRouter(
    tags=["Customers"]
)

@router.get("/customer", response_model=dict)
def get_all_customers(
    offset: int = Query(0),
    limit: int = Query(10),
    customer_service: CustomerProfileService = Depends(get_customer_service),
    access_token: str = Depends(verify_access_token) 
):
    result = customer_service.get_all_customers(limit=limit, offset=offset)
    return {
        "data": [CustomerResponse.from_orm(customer) for customer in result["data"]],
        "total": result["total"]
    }


@router.get("/customer/{customer_id}", response_model=CustomerOut)
def get_customer_by_id(
    customer_id: str, 
    service: CustomerProfileService = Depends(get_customer_service),
    access_token: str = Depends(verify_access_token) 
):
    customer = service.get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer

