# app/routes/chat_history_routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path # Import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from middleware.verify_api_key_header import api_key_auth 
from schemas.chat_history_schema import ChatHistoryResponse, UserHistoryResponse
from uuid import UUID
from fastapi.responses import JSONResponse
from services.report_service import ReportService, get_report_service
from middleware.token_dependency import verify_access_token
from exceptions.custom_exceptions import DatabaseException, ServiceException


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["report"],
)

@router.get("/report/download-csv", dependencies=[Depends(api_key_auth)])
async def read_all_chat_history_endpoint(
    report_type: str = Query(..., description="Jenis report, contoh: CUSTOMER_FEEDBACK"),
    start_date: str = Query(..., description="Tanggal awal format YYYY-MM-DD"),
    end_date: str = Query(..., description="Tanggal akhir format YYYY-MM-DD"),
    report_service: ReportService = Depends(get_report_service),
    access_token: str = Depends(verify_access_token) 
):
    """
    Menghasilkan file CSV dari report_type tertentu dalam rentang tanggal.
    """
    try:
        logger.info(f"[REPORT] Generating report: {report_type} from {start_date} to {end_date}")
        return report_service.report_csv(report_type=report_type, start_date=start_date, end_date=end_date)

    except DatabaseException as e:
        logger.error(f"[REPORT] Database error: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

    except ServiceException as e:
        logger.error(f"[REPORT] Service error: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

    except Exception as e:
        logger.error(f"[REPORT] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"code": "UNEXPECTED_ERROR", "message": "Unexpected error occurred while creating report."})


