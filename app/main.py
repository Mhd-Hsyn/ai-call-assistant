from fastapi import FastAPI
from app.core.database import init_db
# from app.routes import user

app = FastAPI()

# app.include_router(user.router, prefix="/users", tags=["Users"])

@app.on_event("startup")
async def on_startup():
    await init_db()
