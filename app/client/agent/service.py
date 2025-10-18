from uuid import UUID
from retell import Retell
from typing import List
from pydantic import ValidationError
from app.auth.models import UserModel
from app.config.settings import settings
from app.core.exceptions.base import NotFoundException, AppException
from app.core.exceptions.handlers import handle_retell_error
from ..models import AgentModel, ResponseEngineModel
from .schemas import (
    APIBaseResponse,
    AgentAndEngineCreateResponse,
    AgentResponse,
    AgentResponseSchema,
    CreateAgentAndEngineSchema,
    ResponseEngineResponse,
    UpdateAgentSchema,
    UpdateEngineSchema,
    VoiceResponse,
)


class RetellVoiceService:
    def __init__(self):
        self.client = Retell(api_key=settings.retell_api_key)

    def list_voices(self, language: str | None = None, gender: str | None = None) -> List[VoiceResponse]:
        data = self.client.voice.list() or []
        valid_voices: List[VoiceResponse] = []

        for v in data:
            try:
                voice_dict = v.model_dump() if hasattr(v, "model_dump") else v.__dict__

                if language and voice_dict.get("language") and voice_dict["language"].lower() != language.lower():
                    continue
                if gender and voice_dict.get("gender") and voice_dict["gender"].lower() != gender.lower():
                    continue

                valid_voices.append(VoiceResponse(**voice_dict))
            except Exception as e:
                print(f"Skipped invalid voice entry: {e}")
                continue

        return valid_voices


class RetellAgentService:
    def __init__(self):
        self.client = Retell(api_key=settings.retell_api_key)

    async def create_response_engine(self, payload):
        """Create a Response Engine in Retell"""
        try:
            return self.client.llm.create(
                start_speaker=payload.start_speaker,
                general_prompt=payload.general_prompt,
                knowledge_base_ids=payload.knowledge_base_ids,
                model_temperature=payload.temperature,
                model=payload.voice_model,
            )
        except Exception as e:
            raise handle_retell_error(e)

    async def create_agent(self, llm_id: str, payload):
        """Create an Agent linked to a Response Engine in Retell"""
        try:
            return self.client.agent.create(
                response_engine={"llm_id": llm_id, "type": "retell-llm"},
                agent_name=payload.agent_name,
                voice_id=payload.voice_id,
                language=payload.language,
            )
        except Exception as e:
            raise handle_retell_error(e)

    async def update_response_engine(self, engine_id: str, payload, existing_engine):
        """Update Response Engine on Retell"""
        try:
            return self.client.llm.update(
                llm_id=engine_id,
                start_speaker=payload.start_speaker or "user",
                general_prompt=payload.general_prompt or existing_engine.general_prompt,
                knowledge_base_ids=payload.knowledge_base_ids or existing_engine.knowledge_base_ids,
                model_temperature=payload.temperature or existing_engine.temperature,
                model=payload.voice_model or existing_engine.voice_model,
                begin_message=payload.begin_message or None,
            )
        except Exception as e:
            raise handle_retell_error(e)

    async def update_agent(self, agent_id: str, payload, existing_agent):
        """Update Agent on Retell"""
        try:
            return self.client.agent.update(
                agent_id=agent_id,
                agent_name=payload.agent_name or existing_agent.agent_name,
                voice_id=payload.voice_id or existing_agent.voice_id,
                language=payload.language or existing_agent.language,
            )
        except Exception as e:
            raise handle_retell_error(e)

    async def delete_agent(self, agent_id: str):
        """Delete Agent from Retell"""
        try:
            return self.client.agent.delete(agent_id)
        except Exception as e:
            raise handle_retell_error(e)

    async def delete_response_engine(self, engine_id: str):
        """Delete Response Engine from Retell"""
        try:
            return self.client.llm.delete(engine_id)
        except Exception as e:
            raise handle_retell_error(e)


class AgentService:
    def __init__(self):
        self.retell_service = RetellAgentService()

    async def create_agent_and_engine(self, payload: CreateAgentAndEngineSchema, user: UserModel):
        """
        Create Response Engine and Agent in Retell,
        then save both in the local database.
        """
        llm_response = await self.retell_service.create_response_engine(payload)

        engine = ResponseEngineModel(
            user=user,
            engine_id=llm_response.llm_id,
            general_prompt=payload.general_prompt,
            knowledge_base_ids=payload.knowledge_base_ids,
            temperature=payload.temperature,
            voice_model=payload.voice_model,
        )
        await engine.insert()

        agent_response = await self.retell_service.create_agent(llm_response.llm_id, payload)

        agent = AgentModel(
            user=user,
            response_engine=engine,
            agent_id=agent_response.agent_id,
            agent_name=payload.agent_name,
            voice_id=payload.voice_id,
            voice_id_data=payload.voice_id_data,
            language=payload.language,
        )
        await agent.insert()

        response_data = AgentAndEngineCreateResponse(
            engine=ResponseEngineResponse.model_validate(engine),
            agent=AgentResponse.model_validate(agent),
        )

        return APIBaseResponse(
            status=True,
            message="Response Engine and Agent created successfully",
            data=response_data,
        )

    async def update_response_engine(self, retell_engine_llm_id: str, payload: UpdateEngineSchema, user: UserModel):
        """Update Response Engine on Retell and in DB"""
        engine = await ResponseEngineModel.find_one(
            ResponseEngineModel.engine_id == retell_engine_llm_id,
            ResponseEngineModel.user.id == user.id,
        )
        if not engine:
            raise NotFoundException("Response Engine not found")

        await self.retell_service.update_response_engine(retell_engine_llm_id, payload, engine)

        update_data = {
            key: value
            for key, value in payload.dict(exclude_unset=True).items()
            if value is not None
        }

        for key, value in update_data.items():
            setattr(engine, key, value)
        
        try:
            engine = ResponseEngineModel.model_validate(engine.model_dump())
        except ValidationError as e:
            raise AppException(f"Invalid data: {e.errors()}")
        else:
            await engine.save()

        return APIBaseResponse(
            status=True,
            message="Response Engine updated successfully",
            data=ResponseEngineResponse.model_validate(engine),
        )

    async def update_agent(self, retell_agent_id: str, payload: UpdateAgentSchema, user: UserModel):
        """Update Agent on Retell and in DB"""
        agent = await AgentModel.find_one(
            AgentModel.agent_id == retell_agent_id,
            AgentModel.user.id == user.id,
            fetch_links=True,
        )
        if not agent:
            raise NotFoundException("Agent not found")

        await self.retell_service.update_agent(retell_agent_id, payload, agent)

        update_data = {
            key: value
            for key, value in payload.dict(exclude_unset=True).items()
            if value is not None
        }
        for key, value in update_data.items():
            setattr(agent, key, value)
        
        try:
            agent = AgentModel.model_validate(agent.model_dump())
        except ValidationError as e:
            raise AppException(f"Invalid data: {e.errors()}")
        else:
            await agent.save()

        return APIBaseResponse(
            status=True,
            message="Agent updated successfully",
            data=AgentResponseSchema.model_validate(agent),
        )

    async def delete_agent_and_engine(self, agent_uuid: UUID, user: UserModel):
        """
        Delete Agent and its linked Response Engine from:
        - Retell (both agent and LLM)
        - Local database
        """
        agent = await AgentModel.find_one(
            AgentModel.id == agent_uuid,
            AgentModel.user.id == user.id,
            fetch_links=True,
        )
        if not agent:
            raise NotFoundException("Agent not found")

        engine = agent.response_engine
        if not engine:
            raise NotFoundException("Linked Response Engine not found")

        try:
            await self.retell_service.delete_agent(agent.agent_id)
            await self.retell_service.delete_response_engine(engine.engine_id)
        except Exception as e:
            print(f"Retell delete failed: {e}")

        await agent.delete()
        await engine.delete()

        return APIBaseResponse(
            status=True,
            message="Agent and linked Response Engine deleted successfully",
            data=None,
        )
