from uuid import UUID
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
    APIBaseResponse,
    CreateAgentAndEngineSchema,
    AgentResponseSchema,
    ResponseEngineResponse
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


@agent_router.get("/list", response_model=APIBaseResponse, status_code=status.HTTP_200_OK)
async def list_user_agents(user: UserModel = Depends(ProfileActive())):
    """
    🤖 Get all agents created by the authenticated user.
    Ordered by newest first (created_at DESC)
    """
    agents = (
        await AgentModel.find(AgentModel.user.id == user.id)
        .sort(-AgentModel.created_at)
        .to_list()
    )

    if not agents:
        return APIBaseResponse(
            status=True,
            message="No agents found",
            data=[],
        )

    agent_responses = [AgentResponseSchema(**agent.model_dump()) for agent in agents]

    return APIBaseResponse(
        status=True,
        message="Agents fetched successfully",
        count=len(agent_responses),
        data=agent_responses,
    )


@agent_router.get(
    "/engine-data",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def get_engine_data_by_agent(
    agent_id: UUID = Query(..., description="Agent UUID"),
    user: UserModel = Depends(ProfileActive()),
):
    """
    🎯 Fetch the Response Engine data for a specific Agent using its agent_id.
    Only returns the Response Engine details (no Agent data).
    """
    # Find the agent and fetch the linked response engine
    agent = await AgentModel.find_one(
        AgentModel.id == agent_id,
        AgentModel.user.id == user.id,
        fetch_links=True
    )

    if not agent or not agent.response_engine:
        return APIBaseResponse(
            status=False,
            message="Engine not found for this agent or user",
        )

    engine = agent.response_engine
    response_data=ResponseEngineResponse.model_validate(engine)

    return APIBaseResponse(
        status=True,
        message="Engine data fetched successfully",
        data=response_data,
    )


