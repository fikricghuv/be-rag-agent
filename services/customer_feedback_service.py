# app/services/customer_feedback_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from database.models.customer_feedback_model import CustomerFeedback

class CustomerFeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def fetch_all_feedbacks(self):
        """Mengambil semua data feedback dari database."""
        feedbacks = self.db.execute(select(CustomerFeedback)).scalars().all()
        return feedbacks