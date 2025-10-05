from fastapi import status

class AppException(Exception):
    """Base application exception with message + status code."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code


class NotFoundException(AppException):
    """404 Not Found error."""
    def __init__(self, message="Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class UnauthorizedException(AppException):
    """401 Unauthorized error."""
    def __init__(self, message="Unauthorized"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    """403 Forbidden error."""
    def __init__(self, message="Forbidden"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)
