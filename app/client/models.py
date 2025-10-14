from beanie import Link, Document
from pydantic import Field
from typing import Optional, List
from app.core.models.base import BaseDocument
from app.auth.models import UserModel
from app.core.constants.choices import (
    KnowledgeBaseStatusChoices,
    KnowledgeBaseSourceTypeChoices,
    VoiceModelChoices,
    LanguageChoices,
    EngineStartSpeakChoice
)


class KnowledgeBaseModel(BaseDocument):
    user: Link[UserModel]
    knowledge_base_id: str = Field(..., index=True, unique=True)
    name: str
    status: KnowledgeBaseStatusChoices = KnowledgeBaseStatusChoices.IN_PROGRESS

    class Settings:
        name = "knowledge_bases"


class KnowledgeBaseSourceModel(BaseDocument):
    knowledge_base: Link[KnowledgeBaseModel]
    source_id: str = Field(..., index=True, unique=True)
    type : KnowledgeBaseSourceTypeChoices
    title : str | None = None
    url : str

    class Settings:
        name = "knowledge_base_sources"



class ResponseEngineModel(BaseDocument):
    """
    Stores user-specific Retell LLM (Response Engine) configuration and metadata.
    """

    user: Link[UserModel]
    engine_id: str = Field(..., index=True, unique=True, description="ID from Retell API")
    general_prompt: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = Field(default_factory=list)
    temperature: Optional[float] = 0
    voice_model: Optional[VoiceModelChoices] = Field(
        default=VoiceModelChoices.GPT_4O_MINI,
        description="Voice model variant"
    )
    start_speaker: Optional[EngineStartSpeakChoice] = Field(
        default=EngineStartSpeakChoice.USER,
        description="Who start conversation"
    )

    class Settings:
        name = "response_engines"



class AgentModel(BaseDocument):
    """
    Represents a user's agent linked to a Retell Response Engine.
    """

    user: Link[UserModel]
    response_engine: Link[ResponseEngineModel]
    agent_id: str = Field(..., index=True, unique=True, description="Agent ID from Retell API")
    agent_name: str = Field(..., description="Agent name shown in the app")
    voice_id: str = Field(..., description="Selected voice ID from Retell /voices API")
    language: LanguageChoices = Field(
        default=LanguageChoices.EN_US,
        description="Language code (e.g. en-US, es-ES, fr-FR)"
    )

    class Settings:
        name = "agents"



