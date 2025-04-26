from sqlalchemy.orm import Session
from sqlalchemy import select
from models.customer_feedback_model import CustomerFeedback

def fetch_all_feedbacks(db: Session):
    """Mengambil semua data feedback dari database."""
    feedbacks = db.execute(select(CustomerFeedback)).scalars().all()
    return feedbacks
