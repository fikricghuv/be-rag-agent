import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from schemas.customer_schema import CustomerOut, CustomerResponse
from services.customer_profile_service import CustomerProfileService, get_customer_service
from middleware.token_dependency import verify_access_token_and_get_client_id
from exceptions.custom_exceptions import DatabaseException, ServiceException
from uuid import UUID

router = APIRouter(tags=["Customers"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/customer", response_model=dict)
def get_all_customers(
    offset: int = Query(0),
    limit: int = Query(10),
    search: Optional[str] = Query(None),
    customer_service: CustomerProfileService = Depends(get_customer_service),
    client_id: UUID = Depends(verify_access_token_and_get_client_id) 
):
    try:
        logger.info(f"[CUSTOMER] Get all customers offset={offset}, limit={limit}, search={search}")
        result = customer_service.get_all_customers(limit=limit, offset=offset, search=search, client_id=client_id)
        logger.info(f"[CUSTOMER] Retrieved {len(result['data'])} customers")

        return {
            "data": [CustomerResponse.from_orm(customer) for customer in result["data"]],
            "total": result["total"]
        }

    except DatabaseException as e:
        logger.error(f"[CUSTOMER] Database error: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

    except ServiceException as e:
        logger.error(f"[CUSTOMER] Service error: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

    except Exception as e:
        logger.error(f"[CUSTOMER] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"code": "UNEXPECTED_ERROR", "message": "Unexpected error occurred while retrieving customers."})


@router.get("/customer/{customer_id}", response_model=CustomerOut)
def get_customer_by_id(
    customer_id: str,
    service: CustomerProfileService = Depends(get_customer_service),
    client_id: UUID = Depends(verify_access_token_and_get_client_id) 
):
    try:
        logger.info(f"[CUSTOMER] Get customer by ID: {customer_id}")
        customer = service.get_customer_by_id(customer_id, client_id=client_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CUSTOMER_NOT_FOUND", "message": "Customer not found"}
            )
        return customer

    except DatabaseException as e:
        logger.error(f"[CUSTOMER] Database error: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

    except ServiceException as e:
        logger.error(f"[CUSTOMER] Service error: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error(f"[CUSTOMER] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": "UNEXPECTED_ERROR", "message": "Unexpected error occurred while retrieving customer."}
        )
