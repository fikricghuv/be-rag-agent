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
    def __init__(self, message: str = "A database error occurred", code: str = "DATABASE_ERROR"):
        super().__init__(
            message=message,
            status_code=500,
            code=code
        )


class NotFoundException(ServiceException):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(
            message=message,
            status_code=404,
            code=code
        )


class UnauthorizedException(ServiceException):
    def __init__(self, message: str = "Unauthorized access", code: str = "UNAUTHORIZED"):
        super().__init__(
            message=message,
            status_code=401,
            code=code
        )


class ConflictException(ServiceException):
    def __init__(self, message: str = "Conflict error", code: str = "CONFLICT_ERROR"):
        super().__init__(
            message=message,
            status_code=409,
            code=code
        )


class ValidationException(ServiceException):
    def __init__(self, message: str = "Validation failed", code: str = "VALIDATION_ERROR"):
        super().__init__(
            message=message,
            status_code=422,
            code=code
        )
