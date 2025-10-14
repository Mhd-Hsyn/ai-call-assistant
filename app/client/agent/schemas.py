from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from typing import List, Optional, Any
from app.core.constants.choices import (
    VoiceModelChoices,
    LanguageChoices,
    EngineStartSpeakChoice
)

class APIBaseResponse(BaseModel):
    status: bool
    message: str
    data: Any | None = None


#####  Agent Create Schema  #####

class CreateAgentAndEngineSchema(BaseModel):
    """Schema to create a Response Engine + Agent"""
    
    # Response Engine fields
    general_prompt: Optional[str] = Field(None, description="General prompt for LLM")
    knowledge_base_ids: Optional[List[str]] = Field(default_factory=list, description="Linked Knowledge Base IDs")
    temperature: Optional[float] = Field(0.7, description="Temperature for LLM")
    voice_model: VoiceModelChoices = Field(
        default=VoiceModelChoices.GPT_4O_MINI,
        description="Voice model variant (must match Retell supported models)"
    )
    start_speaker: EngineStartSpeakChoice = Field(
        default=EngineStartSpeakChoice.USER,
        description="Who starts the conversation"
    )

    # Agent fields
    agent_name: str = Field(..., description="Name of the Agent")
    voice_id: str = Field(..., description="Voice ID from Retell /voices API")
    language: LanguageChoices = Field(
        default=LanguageChoices.EN_US,
        description="Language code (e.g. en-US, es-ES, fr-FR)"
    )

    class Config:
        use_enum_values = True  # ✅ auto serialize enums to string



class ResponseEngineResponse(BaseModel):
    """Response schema for Retell Response Engine"""
    id: UUID
    engine_id: str
    general_prompt: Optional[str]
    knowledge_base_ids: List[str] = []
    temperature: Optional[float]
    voice_model: Optional[str]
    start_speaker: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v,
        }


class LinkedEngineInfo(BaseModel):
    id: UUID
    engine_id: str

    class Config:
        orm_mode = True
        from_attributes = True
        json_encoders = {UUID: str}


class AgentResponse(BaseModel):
    """Response schema for Agent"""
    id: UUID
    agent_id: str
    agent_name: str
    voice_id: str
    language: str
    response_engine: LinkedEngineInfo  # ✅ Avoid recursion here
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v,
        }


class AgentAndEngineCreateResponse(BaseModel):
    """Final combined response"""
    engine: ResponseEngineResponse
    agent: AgentResponse



#####  Voice ID Response Schema  #####

class VoiceResponse(BaseModel):
    voice_id: Optional[str] = None
    voice_name: Optional[str] = None
    provider: Optional[str] = None
    gender: Optional[str] = None
    accent: Optional[str] = None
    age: Optional[str] = None
    preview_audio_url: Optional[str] = None
    voice_type: Optional[str] = None
    standard_voice_type: Optional[str] = None
    avatar_url: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None



#####  Retrieve Agent  #####

class AgentResponseSchema(BaseModel):
    id: UUID
    agent_id: str
    agent_name: str
    voice_id: str
    language: str
    created_at: datetime
    updated_at: datetime


