from beanie import Link, Document
from pydantic import Field
from typing import Optional, List
from app.core.models.base import BaseDocument
from app.auth.models import UserModel
from app.core.constants.choices import (
    KnowledgeBaseStatusChoices,
    KnowledgeBaseSourceTypeChoices,
    VoiceModelChoices,
    LanguageChoices
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
    name: str
    general_prompt: Optional[str] = None
    knowledge_base_ids: Optional[List[str]] = Field(default_factory=list)
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024

    class Settings:
        name = "response_engines"



class AgentModel(BaseDocument):
    """
    Represents a user's agent linked to a Retell Response Engine.
    """

    user: Link[UserModel]
    response_engine: Link[ResponseEngineModel]
    agent_id: str = Field(..., index=True, unique=True, description="Agent ID from Retell API")
    name: str = Field(..., description="Agent name shown in the app")
    voice_id: str = Field(..., description="Selected voice ID from Retell /voices API")
    voice_model: Optional[VoiceModelChoices] = Field(
        default=VoiceModelChoices.GPT_4O_MINI,
        description="Voice model variant"
    )
    language: LanguageChoices = Field(
        default=LanguageChoices.EN_US,
        description="Language code (e.g. en-US, es-ES, fr-FR)"
    )

    class Settings:
        name = "agents"



