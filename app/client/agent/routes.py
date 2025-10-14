from fastapi import (
    APIRouter, 
    Request, 
    status, 
    UploadFile, 
    Body, 
    Depends, 
)
from app.config.settings import settings
from app.core.exceptions.base import (
    AppException,
    InternalServerErrorException,
    ToManyRequestExeption,
    NotFoundException,
)
from app.core.dependencies.authentication import (
    JWTAuthentication
)
from app.core.dependencies.authorization import (
    EmailVerified, 
    ProfileActive
)
from app.core.constants.choices import (
    KnowledgeBaseStatusChoices,
    KnowledgeBaseSourceTypeChoices
)
from app.auth.models import (
    UserModel
)
from ..models import (
    ResponseEngineModel,
    AgentModel
    
)
from app.core.utils.save_images import (
    save_profile_image
)
from .schemas import (
    APIBaseResponse,
    CreateAgentAndEngineSchema
)
from .service import (
    AgentService
)

agent_router = APIRouter()

@agent_router.post(
    "/create",
    response_model=None,
    status_code=status.HTTP_201_CREATED
)
async def create_agent_and_engine(
    payload: CreateAgentAndEngineSchema,
    user: UserModel = Depends(ProfileActive())
):
    """
    🧠 Create a Response Engine and a linked Agent in Retell & save in DB
    """
    agent_service = AgentService()
    return await agent_service.create_agent_and_engine(payload, user)



