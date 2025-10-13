import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.settings import MEDIA_DIR
from app.config.logger import get_logger
from app.config.routers import include_all_routers
from app.config.lifespan import lifespan
from app.config.cors import setup_cors
from app.config.middleware import setup_middlewares
from app.config.exceptions import setup_exceptions


logger = get_logger("main")



# Create FastAPI instance
app = FastAPI(
    title="AI Call Assistant Backend",
    description="API backend for Call Assitant AI platform",
    version="1.0.0",
    lifespan=lifespan,
)

include_all_routers(app)
setup_cors(app)
setup_exceptions(app)
setup_middlewares(app)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")




if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )



