from uuid import UUID
from typing import Optional
from beanie.operators import In
from fastapi import (
    APIRouter, 
    status, 
    Query, 
    Depends, 
)
from app.config.settings import settings
from app.core.exceptions.base import (
    BadGatewayException,
    NotFoundException,
    BadGatewayException,
    InternalServerErrorException,
)
from app.core.dependencies.authorization import (
    ProfileActive
)
from app.auth.models import (
    UserModel
)
from ..models import (
    AgentModel,
    KnowledgeBaseModel,
    ResponseEngineModel,
    MeetingWorkflowModel
)
from .schemas import (
    APIBaseResponse,
    CreateAgentAndEngineSchema,
    AgentResponseSchema,
    ResponseEngineResponse,
    KnowledgeBaseInfoResponse,
    UpdateEngineSchema,
    UpdateAgentSchema,
    CreateMeetingWorkflowPayload,
    PhoneNumberUpdatePayload,

)
from .service import (
    AgentService,
    RetellVoiceService,
    RetellAgentService
)
from app.config.logger import get_logger
from .utils import map_payload_to_retell_states

logger = get_logger("Agent Routes")

agent_router = APIRouter()



@agent_router.get("/voices", status_code=status.HTTP_200_OK)
async def list_voices(
    language: Optional[str] = Query(None, description="Filter by language code, e.g. en-US"),
    gender: Optional[str] = Query(None, description="Filter by gender (male/female)")
):
    """
    List available Retell voices  
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
    Create a Response Engine and a linked Agent in Retell & save in DB
    """
    agent_service = AgentService()
    return await agent_service.create_agent_and_engine(payload, user)


@agent_router.get("/list", response_model=APIBaseResponse, status_code=status.HTTP_200_OK)
async def list_user_agents(user: UserModel = Depends(ProfileActive())):
    """
    Get all agents created by the authenticated user.
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

    agent_responses = [
        AgentResponseSchema.model_validate(agent) for agent in agents
    ]

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
    Fetch the Response Engine data for a specific Agent using its agent_id.
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



@agent_router.get(
    "/agent-data",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def get_agent_data_by_id(
    agent_id : UUID = Query(..., description="Agent UUID"),
    user : UserModel = Depends(dependency=ProfileActive())
):
    agent = await AgentModel.find_one(
        AgentModel.id == agent_id,
        AgentModel.user.id == user.id
    )
    if not agent:
        raise NotFoundException("agent not found")

    agent_data = AgentResponseSchema.model_validate(agent)
    return APIBaseResponse(
        status= True,
        message= "Agent data retrive successfully",
        data=agent_data
    )


@agent_router.get(
    "/engine-knowledgebase",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def get_agent_engine_knowledgebases(
    agent_id : UUID = Query(..., description="Agent UUID"),
    user : UserModel = Depends(dependency=ProfileActive())
):
    agent = await AgentModel.find_one(
        AgentModel.id == agent_id,
        AgentModel.user.id == user.id,
        fetch_links=True
    )
    response_engine = agent.response_engine
    if not agent or not response_engine:
        raise NotFoundException("Agent or Engine not found")

    knowledge_base_ids = response_engine.knowledge_base_ids
    knowledge_bases = await KnowledgeBaseModel.find(
        In(KnowledgeBaseModel.knowledge_base_id, knowledge_base_ids)
    ).to_list()
    data = [KnowledgeBaseInfoResponse.model_validate(kb) for kb in knowledge_bases]

    return APIBaseResponse(
        status=True,
        message= "Knowledge Base retrive successfully",
        data= data
    )

# update

@agent_router.patch(
    "/update-engine/{retell_engine_llm_id}",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def update_response_engine(
    retell_engine_llm_id: str,
    payload: UpdateEngineSchema,
    user: UserModel = Depends(ProfileActive())
):
    """
    Update Response Engine on Retell and in DB
    """
    service = AgentService()
    return await service.update_response_engine(retell_engine_llm_id, payload, user)


@agent_router.patch(
    "/update-agent/{retell_agent_id}",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def update_agent(
    retell_agent_id: str,
    payload: UpdateAgentSchema,
    user: UserModel = Depends(ProfileActive())
):
    """
    Update Agent on Retell and in DB
    """
    service = AgentService()
    return await service.update_agent(retell_agent_id, payload, user)


# delete

@agent_router.delete("/delete", response_model=APIBaseResponse)
async def delete_agent_and_engine(
    agent_id : UUID = Query(..., description="Agent UUID"),
    user: UserModel = Depends(ProfileActive())
):
    """
    Delete agent + linked response engine from Retell & DB
    """
    service = AgentService()
    return await service.delete_agent_and_engine(agent_id, user)




@agent_router.get("/user-id", response_model=APIBaseResponse)
async def get_user_id_by_agent(
    agent_id : UUID = Query(..., description="Agent UUID"),
):
    """
    🔍 Get the User ID linked to a given Retell Agent ID.
    """
    # Find the agent by agent_id
    agent = await AgentModel.find_one(AgentModel.id == agent_id, fetch_links=True)
    if not agent:
        raise NotFoundException(
            "Agent not found"
        )

    # Extract the linked user
    user = agent.user  # Because fetch_links=True, user is already loaded
    if not user:
        raise NotFoundException(
            "Linked user not found"
        )

    return APIBaseResponse(
        status=True,
        message="User found successfully",
        data={
            "user_id": str(user.id),
            "user_email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    )


# Calender meeting integrate




@agent_router.post("/meeting/workflow")
async def create_or_update_workflow(
    payload: CreateMeetingWorkflowPayload,
    user: UserModel = Depends(ProfileActive())
):
    # 1) Validate agent & fetch links to get response_engine
    agent = await AgentModel.find_one(
        AgentModel.agent_id == payload.agent_id,
        AgentModel.user.id == user.id,
        fetch_links=True
    )
    if not agent:
        raise NotFoundException("Agent not found")

    # get engine id from agent.response_engine
    engine_link = agent.response_engine
    engine = None
    if hasattr(engine_link, "id"):
        engine = await ResponseEngineModel.get(engine_link.id)
    else:
        # fallback: try query by id saved
        engine = await ResponseEngineModel.find_one(ResponseEngineModel.id == engine_link)

    if not engine:
        raise NotFoundException("Response engine for agent not found")

    engine_id = engine.engine_id

    # 2) Save raw payload into DB and normalize states
    # Convert incoming pydantic objects to plain dicts
    raw_payload = payload.model_dump()
    data_list = raw_payload.get("data", [])

    # Build retell-compatible states list using mapper
    retell_states = map_payload_to_retell_states(data_list)

    # Determine starting state (first state's name)
    starting_state = retell_states[0]["name"] if retell_states else "introduction"

    # 3) Create or update MeetingWorkflowModel by agent
    existing = await MeetingWorkflowModel.find_one(MeetingWorkflowModel.agent.id == agent.id)

    if existing:
        existing.raw_payload = raw_payload
        existing.states_normalized = retell_states
        existing.engine_id = engine_id
        await existing.save()
        workflow = existing
        db_message = "Workflow updated successfully"
    else:
        workflow = MeetingWorkflowModel(
            agent=agent,
            engine_id=engine_id,
            raw_payload=raw_payload,
            states_normalized=retell_states
        )
        await workflow.insert()
        db_message = "Workflow created successfully"

    # 4) Sync to Retell (service)
    retell_service = RetellAgentService()
    try:
        await retell_service.update_retell_llm(
            engine_id=engine_id,
            states=retell_states,
            starting_state=starting_state
        )
        retell_sync = True
    except Exception as e:
        # optional: roll back DB change or set a "synced": False flag
        # Here we keep DB but inform caller of failure
        retell_sync = False
        # log error in real app
        raise BadGatewayException(f"Retell sync failed: {e}")

    return {
        "status": True,
        "message": db_message,
        "workflow_id": str(workflow.id),
        "retell_sync": retell_sync
    }



@agent_router.get("/meeting/workflow")
async def get_workflow_by_agent(
    agent_id: str = Query(...),
    user: UserModel = Depends(ProfileActive())
):
    """
    Fetch MeetingWorkflow by agent_id
    Returns raw payload and normalized states
    """

    agent = await AgentModel.find_one(
        AgentModel.agent_id == agent_id,
        AgentModel.user.id == user.id
    )
    if not agent:
        raise NotFoundException("Agent not found")

    workflow = await MeetingWorkflowModel.find_one(MeetingWorkflowModel.agent.id == agent.id)
    if not workflow:
        raise NotFoundException("Workflow not found")

    return {
        "status": True,
        "agent_id": agent_id,
        "workflow_id": str(workflow.id),
        "raw_payload": workflow.raw_payload,
        "states_normalized": workflow.states_normalized
    }



@agent_router.post("/phone-number/update")
async def update_phone_number(
    payload: PhoneNumberUpdatePayload,
    user: UserModel = Depends(ProfileActive())
):
    agent = await AgentModel.find_one(
        AgentModel.agent_id == payload.agent_id,
        AgentModel.user.id == user.id,
        fetch_links=True
    )
    if not agent:
        raise NotFoundException("Agent not found")

    try:
        # Assuming you have a RetellAgentService class initialized
        retell_service = RetellAgentService()
        phone_number_response = retell_service.update_agent_inbound(
            inbound_agent_id=agent.agent_id,
            phone_number=payload.phone_number,
            nickname=payload.nickname,
        )
    except Exception as e:
        raise InternalServerErrorException(f"Retell API error: {str(e)}")

    return {
        "status": True,
        "message": "Phone number updated successfully",
        "data": phone_number_response
    }


