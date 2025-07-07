# app/exceptions/custom_exceptions.py

class ServiceException(Exception):
    """
    Base class for service-level exceptions with optional HTTP status and error code.
    """
    def __init__(
        self,
        message: str = "A service error occurred",
        status_code: int = 400,
        code: str = "SERVICE_ERROR"
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class DatabaseException(ServiceException):
    def __init__(self, message: str = "A database error occurred"):
        super().__init__(
            message=message,
            status_code=500,
            code="DATABASE_ERROR"
        )


class NotFoundException(ServiceException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=404,
            code="NOT_FOUND"
        )


class UnauthorizedException(ServiceException):
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            message=message,
            status_code=401,
            code="UNAUTHORIZED"
        )


class ConflictException(ServiceException):
    def __init__(self, message: str = "Conflict error"):
        super().__init__(
            message=message,
            status_code=409,
            code="CONFLICT_ERROR"
        )


class ValidationException(ServiceException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(
            message=message,
            status_code=422,
            code="VALIDATION_ERROR"
        )
