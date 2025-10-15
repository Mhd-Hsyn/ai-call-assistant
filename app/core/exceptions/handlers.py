from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette import status
from .base import AppException


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": False, "message": exc.message},
    )


# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     errors = []
#     for err in exc.errors():
#         field = err["loc"][-1]
#         msg = err["msg"]
#         errors.append({field: msg})

#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
#         content={
#             "status": False,
#             "message": "Validation failed",
#             "errors": errors,
#         },
#     )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    message_parts = []

    for err in exc.errors():
        loc = err.get("loc", ())
        field = loc[-1] if loc else "non_field_error"
        msg = err.get("msg", "Invalid input")

        errors.append({field: msg})
        message_parts.append(f"{field} {msg}")

    summary_message = "Validation failed"
    if message_parts:
        summary_message += ", " + ", ".join(message_parts)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": False,
            "message": summary_message,
            "errors": errors,
        },
    )


def handle_retell_error(e: Exception) -> AppException:
    """Parse and format Retell API errors for clean API response."""
    import ast
    from fastapi import status

    error_text = str(e)
    message = "An unexpected error occurred with Retell API."

    # Try extracting structured JSON/dict-like message
    if "Error code:" in error_text:
        try:
            # Split after the first '-' to get the dict-like portion
            json_part = error_text.split("-", 1)[1].strip()
            parsed = ast.literal_eval(json_part)  # Safely convert string to dict

            # Check common keys used by Retell API
            message = (
                parsed.get("message")
                or parsed.get("error")
                or parsed.get("error_message")
                or message
            )
        except Exception:
            # If parsing fails, fallback to raw error
            message = error_text
    else:
        message = error_text

    return AppException(message, status.HTTP_400_BAD_REQUEST)



async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": False, "message": str(exc.detail)},
    )
