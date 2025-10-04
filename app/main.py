from fastapi import FastAPI
from app.config.database import init_db
from app.auth.routes import auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])


@app.on_event("startup")
async def on_startup():
    await init_db()
