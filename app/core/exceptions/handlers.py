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
        field = err["loc"][-1]
        msg = err["msg"]

        # add in error list
        errors.append({field: msg})

        # add to message summary
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




async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": False, "message": str(exc.detail)},
    )
