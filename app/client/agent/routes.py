from fastapi import (
    APIRouter, 
    Request, 
    status, 
    UploadFile, 
    Query, 
    Depends, 
)
from typing import Optional
from app.config.settings import settings
from app.core.exceptions.base import (
    AppException,
    BadGatewayException,

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
    VoiceResponse,
    CreateAgentAndEngineSchema
)
from .service import (
    AgentService,
    RetellVoiceService
    
)

agent_router = APIRouter()



@agent_router.get("/voices", status_code=status.HTTP_200_OK)
async def list_voices(
    language: Optional[str] = Query(None, description="Filter by language code, e.g. en-US"),
    gender: Optional[str] = Query(None, description="Filter by gender (male/female)")
):
    """
    🎙️ List available Retell voices  
    Optionally filter by language or gender.
    """
    try:
        voice_service = RetellVoiceService()
        voices = voice_service.list_voices(language=language, gender=gender)
        return {
            "status": True,
            "message": "Voices fetched successfully",
            "count": len(voices),
            "data": [v.model_dump() for v in voices],
        }
    except Exception as e:
        raise BadGatewayException(f"Failed to fetch voices from Retell: {e}")


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



