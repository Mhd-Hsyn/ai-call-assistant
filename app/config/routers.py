from fastapi import FastAPI
from app.auth.routes import auth_router
from app.client.routes import client_router

API_PREFIX = "/api"

def include_all_routers(app: FastAPI):
    app.include_router(auth_router, prefix=f"{API_PREFIX}/auth", tags=["Auth"])
    app.include_router(client_router, prefix=f"{API_PREFIX}/clientside", tags=["Client Side"])

