# app/exceptions/exception_utils.py

from sqlalchemy.exc import SQLAlchemyError
from exceptions.custom_exceptions import DatabaseException

def handle_db_error(e: Exception):
    if isinstance(e, SQLAlchemyError):
        raise DatabaseException("Database operation failed.")
    raise e
