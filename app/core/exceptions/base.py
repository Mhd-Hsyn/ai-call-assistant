from fastapi import status

class AppException(Exception):
    """Base application exception with message + status code."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code


class ToManyRequestExeption(AppException):
    def __init__(self, message: str, status_code: int = status.HTTP_429_TOO_MANY_REQUESTS):
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


class InternalServerErrorException(AppException):
    """500 Internal Server Error."""
    def __init__(self, message="Internal server error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)



class BadGatewayException(AppException):
    """502 Bad Gateway Error."""
    def __init__(self, message="Internal server error"):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY)



