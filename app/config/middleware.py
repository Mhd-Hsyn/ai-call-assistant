import time
from fastapi import Request
from app.config.logger import get_logger

logger = get_logger("middleware")


def setup_middlewares(app):
    """Attach custom middlewares (like logging)."""

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Logs incoming requests with response time."""
        start_time = time.time()
        logger.info(f"➡️  {request.method} {request.url.path}")

        response = await call_next(request)

        duration = (time.time() - start_time) * 1000
        logger.info(
            f"✅ {request.method} {request.url.path} "
            f"→ {response.status_code} | {duration:.2f}ms"
        )
        return response



