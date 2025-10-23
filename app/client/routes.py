from fastapi import (
    APIRouter
)
from .knowledge_base.routes import (
    knowledge_base_router
)
from .agent.routes import (
    agent_router
)
from .calls.routes import (
    calls_router
)
from .pricing.routes import (
    pricing_router
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
client_router.include_router(
    calls_router,
    prefix="/calls",
    tags=['Calls']
)
client_router.include_router(
    router=pricing_router,
    prefix='/pricing',
    tags=['Pricing']
)

