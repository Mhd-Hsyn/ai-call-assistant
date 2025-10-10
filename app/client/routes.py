from fastapi import (
    APIRouter
)
from .knowledge_base.routes import (
    knowledge_base_router
)
from .agent.routes import (
    agent_router
)

client_router = APIRouter()

client_router.include_router(
    knowledge_base_router,
    prefix="/knowledge-base",
    tags=["Knowledge Base"],
)
client_router.include_router(
    agent_router,
    prefix="/agent",
    tags=["Agent"],
)


