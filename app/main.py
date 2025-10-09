import uvicorn
import time
from pydantic import ValidationError
from fastapi import FastAPI, Request
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
from app.config.logger_config import get_logger
from fastapi.middleware.cors import CORSMiddleware

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    try:
        otp_client.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"❌ Redis connection failed: __________ {e}")

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



# Allowed origins
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Kon kon se origins allowed hain
    allow_credentials=True,         # Cookies, Authorization headers allow karne ke liye
    allow_methods=["*"],            # GET, POST, PUT, DELETE sab allow
    allow_headers=["*"],            # All headers allow
)



# ---------------- Middleware for Logging ----------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log each request and its response time."""
    start_time = time.time()
    logger.info(f"➡️  Request started: {request.method} {request.url}")

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_time = f"{process_time:.2f}ms"

    logger.info(
        f"✅ Request completed: {request.method} {request.url.path} "
        f"Status: {response.status_code} | Time: {formatted_time}"
    )
    return response



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


