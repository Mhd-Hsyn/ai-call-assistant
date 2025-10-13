from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
from app.core.exceptions.base import AppException
from app.core.exceptions.handlers import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
)


def setup_exceptions(app):
    """Register global exception handlers."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

