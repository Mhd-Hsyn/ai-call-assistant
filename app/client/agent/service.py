from retell import Retell
from app.config.settings import settings
from app.auth.models import UserModel
from app.core.exceptions.base import AppException
from app.core.exceptions.handlers import handle_retell_error
from ..models import AgentModel,ResponseEngineModel
from .schemas import (
    CreateAgentAndEngineSchema, 
    APIBaseResponse,
    AgentAndEngineCreateResponse,
    ResponseEngineResponse,
    AgentResponse

)


class RetellAgentCreateService:
    def __init__(self):
        self.client = Retell(api_key=settings.retell_api_key)

    async def create_response_engine(self, payload):
        """🔹 Create a Response Engine in Retell"""
        try:
            return self.client.llm.create(
                start_speaker=payload.start_speaker,
                general_prompt=payload.general_prompt,
                knowledge_base_ids=payload.knowledge_base_ids,
                model_temperature=payload.temperature,
                model=payload.voice_model
            )
        except Exception as e:
            raise handle_retell_error(e)


    async def create_agent(self, llm_id: str, payload):
        """🔹 Create an Agent linked to a Response Engine in Retell"""
        try:
            return self.client.agent.create(
                response_engine={
                    "llm_id": llm_id,
                    "type": "retell-llm"
                },
                agent_name = payload.agent_name,
                voice_id=payload.voice_id,
                language=payload.language
            )
        except Exception as e:
            raise handle_retell_error(e)


class AgentService:
    def __init__(self):
        self.retell_service = RetellAgentCreateService()

    async def create_agent_and_engine(self, payload: CreateAgentAndEngineSchema, user: UserModel):
        """
        🔹 Create Response Engine in Retell
        🔹 Save it to DB
        🔹 Create Agent in Retell
        🔹 Save Agent in DB
        """

        # Step 1: Create Engine on Retell
        llm_response = await self.retell_service.create_response_engine(payload)

        # Step 2: Save Engine in DB
        engine = ResponseEngineModel(
            user=user,
            engine_id=llm_response.llm_id,
            general_prompt=payload.general_prompt,
            knowledge_base_ids=payload.knowledge_base_ids,
            temperature=payload.temperature,
            voice_model=payload.voice_model
        )
        await engine.insert()

        # Step 3: Create Agent on Retell
        agent_response = await self.retell_service.create_agent(llm_response.llm_id, payload)

        # Step 4: Save Agent in DB
        agent = AgentModel(
            user=user,
            response_engine=engine,
            agent_id=agent_response.agent_id,
            agent_name=payload.agent_name,
            voice_id=payload.voice_id,
            language=payload.language
        )
        await agent.insert()

        # Step 5: Return Response
        response_data = AgentAndEngineCreateResponse(
            engine=ResponseEngineResponse.model_validate(engine),
            agent=AgentResponse.model_validate(agent)
        )

        return APIBaseResponse(
            status=True,
            message="Response Engine and Agent created successfully",
            data=response_data
        )
        
