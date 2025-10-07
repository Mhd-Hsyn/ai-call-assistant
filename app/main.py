import uvicorn
import redis
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config.database import init_db
from app.config.settings import MEDIA_DIR
from app.auth.routes import auth_router
from app.core.exceptions.base import AppException
from app.core.exceptions.handlers import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler
)
from app.core.redis_utils.otp_handler.config import otp_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    try:
        otp_client.ping()
        print("✅ Redis connected")
    except redis.ConnectionError:
        print("❌ Redis connection failed")

    await init_db()
    yield
    # --- Shutdown ---
    otp_client.close()
    print("App shutting down...")


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)

# media
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


