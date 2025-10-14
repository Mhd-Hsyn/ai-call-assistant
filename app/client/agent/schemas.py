from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from typing import List, Optional, Any


class APIBaseResponse(BaseModel):
    status: bool
    message: str
    data: Any | None = None



class CreateAgentAndEngineSchema(BaseModel):
    general_prompt: Optional[str] = Field(None, description="General prompt for LLM")
    knowledge_base_ids: Optional[List[str]] = Field(default_factory=list, description="Linked KB IDs")
    temperature: Optional[float] = Field(0.7, description="Temperature for LLM")
    voice_model: Optional[str] = Field("gpt-4o-mini", description="Voice model variant")
    start_speaker: Optional[str] = Field("gpt-4o-mini", description="Voice model variant")

    # Agent details
    agent_name: str = Field(..., description="Name of the Agent")
    voice_id: str = Field(..., description="Voice ID from Retell /voices API")
    language: Optional[str] = Field("en-US", description="Language code")



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

