from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config.database import init_db
from app.auth.routes import auth_router
import uvicorn

app = FastAPI()

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    await init_db()
    yield
    # --- Shutdown ---
    print("App shutting down...")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


