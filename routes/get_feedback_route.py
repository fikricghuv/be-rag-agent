from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from config.config_db import config_db
from models.customer_feedback_model import CustomerFeedback
from models.customer_feedback_response_schema import CustomerFeedbackResponse

router = APIRouter()

# Endpoint Get Customer Feedback
@router.get("/feedbacks", response_model=list[CustomerFeedbackResponse])
def get_feedbacks(db: Session = Depends(config_db)):
    feedbacks = db.execute(select(CustomerFeedback)).scalars().all()
    return feedbacks
