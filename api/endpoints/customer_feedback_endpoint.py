# app/api/endpoints/customer_feedback_endpoint.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.config_db import config_db
from schemas.customer_feedback_response_schema import CustomerFeedbackResponse
from services.customer_feedback_service import CustomerFeedbackService

router = APIRouter()

def get_customer_feedback_service(db: Session = Depends(config_db)):
    return CustomerFeedbackService(db)

@router.get("/feedbacks", response_model=List[CustomerFeedbackResponse])
def get_feedbacks_endpoint(
    customer_feedback_service: CustomerFeedbackService = Depends(get_customer_feedback_service)
):
    try:
        return customer_feedback_service.fetch_all_feedbacks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")