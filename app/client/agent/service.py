from uuid import UUID
from retell import Retell
from typing import List
from app.config.settings import settings
from app.auth.models import UserModel
from app.core.exceptions.base import NotFoundException
from app.core.exceptions.handlers import handle_retell_error
from ..models import AgentModel,ResponseEngineModel
from .schemas import (
    VoiceResponse,
    CreateAgentAndEngineSchema, 
    APIBaseResponse,
    AgentAndEngineCreateResponse,
    ResponseEngineResponse,
    AgentResponse,
    UpdateEngineSchema,
    UpdateAgentSchema,
    AgentResponseSchema,

)



class RetellVoiceService:
    def __init__(self):
        self.client = Retell(api_key=settings.retell_api_key)

    def list_voices(self, language: str | None = None, gender: str | None = None) -> List[VoiceResponse]:
        data = self.client.voice.list() or []
        valid_voices: List[VoiceResponse] = []

        for v in data:
            try:
                # Convert SDK object → dict
                voice_dict = v.model_dump() if hasattr(v, "model_dump") else v.__dict__

                # Optional filters
                if language and voice_dict.get("language") and voice_dict["language"].lower() != language.lower():
                    continue
                if gender and voice_dict.get("gender") and voice_dict["gender"].lower() != gender.lower():
                    continue

                valid_voices.append(VoiceResponse(**voice_dict))
            except Exception as e:
                print(f"⚠️ Skipped invalid voice entry: {e}")
                continue

        return valid_voices



class RetellAgentService:
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
        self.retell_service = RetellAgentService()

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

        # Step 4: Save Agent in DB (with full voice object)
        agent = AgentModel(
            user=user,
            response_engine=engine,
            agent_id=agent_response.agent_id,
            agent_name=payload.agent_name,
            voice_id=payload.voice_id,
            voice_id_data=payload.voice_id_data,
            language=payload.language
        )
        await agent.insert()

        # Step 5: Return response
        response_data = AgentAndEngineCreateResponse(
            engine=ResponseEngineResponse.model_validate(engine),
            agent=AgentResponse.model_validate(agent)
        )

        return APIBaseResponse(
            status=True,
            message="Response Engine and Agent created successfully",
            data=response_data
        )

    async def update_response_engine(self, engine_id: str, payload: UpdateEngineSchema, user: UserModel):
        """
        🔹 Update Response Engine on Retell
        🔹 Update same in DB
        """
        # 1️⃣ Find engine in DB
        engine = await ResponseEngineModel.find_one(
            ResponseEngineModel.engine_id == engine_id,
            ResponseEngineModel.user.id == user.id
        )
        if not engine:
            raise NotFoundException("Response Engine not found")

        # 2️⃣ Update on Retell
        try:
            retell_client = Retell(api_key=settings.retell_api_key)
            updated_llm = retell_client.llm.update(
                llm_id=engine_id,
                start_speaker=payload.start_speaker or "user",
                general_prompt=payload.general_prompt or engine.general_prompt,
                knowledge_base_ids=payload.knowledge_base_ids or engine.knowledge_base_ids,
                model_temperature=payload.temperature or engine.temperature,
                model=payload.voice_model or engine.voice_model,
                begin_message=payload.begin_message or None
            )
        except Exception as e:
            raise handle_retell_error(e)

        # 3️⃣ Update in DB
        update_data = payload.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(engine, key, value)
        await engine.save()

        return APIBaseResponse(
            status=True,
            message="Response Engine updated successfully",
            data=ResponseEngineResponse.model_validate(engine)
        )


    async def update_agent(self, agent_id: str, payload: UpdateAgentSchema, user: UserModel):
        """
        🔹 Update Agent on Retell
        🔹 Update same in DB
        """
        # 1️⃣ Find agent in DB
        agent = await AgentModel.find_one(
            AgentModel.agent_id == agent_id,
            AgentModel.user.id == user.id,
            fetch_links=True
        )
        if not agent:
            raise NotFoundException("Agent not found")

        # 2️⃣ Update on Retell
        try:
            retell_client = Retell(api_key=settings.retell_api_key)
            updated_agent = retell_client.agent.update(
                agent_id=agent_id,
                agent_name=payload.agent_name or agent.agent_name,
                voice_id=payload.voice_id or agent.voice_id,
                language=payload.language or agent.language
            )
        except Exception as e:
            raise handle_retell_error(e)

        # 3️⃣ Update in DB
        update_data = payload.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(agent, key, value)
        await agent.save()

        return APIBaseResponse(
            status=True,
            message="Agent updated successfully",
            data=AgentResponseSchema.model_validate(agent)
        )


