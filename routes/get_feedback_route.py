from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config.config_db import config_db
from controllers.customer_feedback_controller import fetch_all_feedbacks
from models.customer_feedback_response_schema import CustomerFeedbackResponse

router = APIRouter()

@router.get("/feedbacks", response_model=list[CustomerFeedbackResponse])
def get_feedbacks(db: Session = Depends(config_db)):
    return fetch_all_feedbacks(db)
