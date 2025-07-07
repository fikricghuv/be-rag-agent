# utils/exception_handler.py
from fastapi import HTTPException
from functools import wraps
from exceptions.custom_exceptions import DatabaseException, ServiceException
import logging

logger = logging.getLogger(__name__)

def handle_exceptions(tag="[API]"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException as e:
                raise e
            except DatabaseException as e:
                logger.error(f"{tag} DatabaseException: {e.message}", exc_info=True)
                raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
            except ServiceException as e:
                logger.error(f"{tag} ServiceException: {e.message}", exc_info=True)
                raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
            except Exception as e:
                logger.error(f"{tag} Unexpected Error: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail={"code": "UNEXPECTED_ERROR", "message": str(e)})
        return wrapper
    return decorator
