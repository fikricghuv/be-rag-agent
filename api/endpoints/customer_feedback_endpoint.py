# app/api/endpoints/customer_feedback_endpoint.py
import logging # Import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query # Import Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from typing import List
from core.config_db import config_db
# Asumsi Pydantic model CustomerFeedbackResponse diimpor dari schemas.customer_feedback_response_schema
from schemas.customer_feedback_response_schema import CustomerFeedbackResponse
from services.customer_feedback_service import CustomerFeedbackService, get_customer_feedback_service # Import dependency service
# Asumsi dependency api_key_auth diimpor dari services.verify_api_key_header
from services.verify_api_key_header import api_key_auth

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

router = APIRouter(
    tags=["customer-feedback"], # Tag untuk dokumentasi Swagger UI
)

# Dependency function untuk menyediakan instance CustomerFeedbackService
# (Sudah ada di service file, tidak perlu didefinisikan ulang di sini)
# def get_customer_feedback_service(db: Session = Depends(config_db)):
#     return CustomerFeedbackService(db)

# Mengubah endpoint dari POST menjadi GET (lebih sesuai untuk mengambil data)
# Menerapkan API Key Authentication dan Pagination
@router.get("/feedbacks", response_model=List[CustomerFeedbackResponse], dependencies=[Depends(api_key_auth)])
async def get_feedbacks_endpoint(
    # Menggunakan dependency untuk mendapatkan instance service
    customer_feedback_service: CustomerFeedbackService = Depends(get_customer_feedback_service),
    # --- Parameter Pagination ---
    offset: int = Query(0, description="Number of items to skip"), # Default 0
    limit: int = Query(100, description="Number of items to return per page", le=200), # Default 100, maks 200
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk mendapatkan semua feedback customer dengan pagination.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        offset: Jumlah item yang akan dilewati.
        limit: Jumlah item per halaman.
    """
    try:
        logger.info(f"Received request for customer feedbacks with offset={offset}, limit={limit}.")
        # Memanggil metode instance dari service, meneruskan parameter pagination
        feedbacks = customer_feedback_service.fetch_all_feedbacks(offset=offset, limit=limit)

        # Pydantic dengan orm_mode=True akan otomatis mengonversi List[CustomerFeedback] menjadi List[CustomerFeedbackResponse]
        logger.info(f"Returning {len(feedbacks)} feedback entries.")
        return feedbacks

    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        # Log error detail di server
        logger.error(f"Database error in get_feedbacks_endpoint: {e}", exc_info=True)
        # Kembalikan respons 500 generik ke klien
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching customer feedbacks."
        )