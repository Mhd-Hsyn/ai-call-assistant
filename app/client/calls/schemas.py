from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import (
    BaseModel,
    Field, 
    computed_field,
)
from typing import (
    Optional, 
    Dict,
    List,
    Any
)


class APIBaseResponse(BaseModel):
    status: bool
    message: str
    data: Any | None = None



class PaginationMeta(BaseModel):
    page_size: int
    page: int
    total_records: int
    total_pages: int
    is_next: bool
    is_previous: bool

class PaginaionResponse(BaseModel):
    status: bool
    message: str
    meta : PaginationMeta
    data: Any | None = None



class CampaignCreatePayloadSchema(BaseModel):
    agent_uid : UUID = Field(..., description="Agent UUID")
    name : str


class AgentShortInfoSchema(BaseModel):
    id : UUID
    agent_id: str
    agent_name: str

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p")
            if isinstance(v, datetime)
            else v,
        }


class CampaignInfoSchema(BaseModel):
    id: UUID
    name: str
    created_at : datetime
    agent: AgentShortInfoSchema

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p")
            if isinstance(v, datetime)
            else v,
        }



class CampaignModifyPayloadSchema(BaseModel):
    campaign_uid : UUID = Field(..., description="Campaign UUID")
    agent_uid : Optional[UUID] = Field(..., description="Agent UUID")
    name : Optional[str]






class CallInitializeSchema(BaseModel):
    from_number: str
    to_number: str
    override_agent_id: Optional[str] = Field(None, alias="override_agent_id")
    retell_llm_dynamic_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)




class CallBaseResponseSchema(BaseModel):
    duration_ms: Optional[int]
    total_duration : Optional[Decimal]
    total_duration_unit_price : Optional[Decimal]
    combined_cost : Optional[Decimal]
    user_sentiment : Optional[str]
    call_successful : Optional[bool]

    @computed_field(return_type=str)
    def formatted_duration(self) -> Optional[str]:
        """Convert duration from milliseconds → HH:MM:SS"""
        if not self.duration_ms:
            return None
        total_seconds = int(self.duration_ms / 1000)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    @computed_field(return_type=float)
    def total_cost_usd(self) -> Optional[float]:
        """Convert combined_cost (in cents) → USD"""
        if self.combined_cost:
            return round(self.combined_cost / 100, 3)
        return None

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p")
            if isinstance(v, datetime)
            else v,
        }


class AgentMiniSchema(BaseModel):
    id: Optional[UUID]
    agent_name: Optional[str]
    agent_id: Optional[str]
    voice_id_data: Optional[dict]
    language: Optional[str]

    class Config:
        from_attributes = True


class CallDisplayInfoResponseSchema(CallBaseResponseSchema):
    id: UUID
    call_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    agent_name: Optional[str]
    call_type: Optional[str]
    direction: Optional[str]
    call_status: Optional[str]
    from_number: Optional[str]
    to_number: Optional[str]
    disconnection_reason: Optional[str]


class CallFullResponseSchema(CallBaseResponseSchema):
    id: UUID
    call_id: str
    # agent: Optional[AgentMiniSchema]

    call_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    call_cost: Optional[Dict[str, Any]] = Field(default_factory=dict)

    agent_name: Optional[str]
    call_type: Optional[str]
    direction: Optional[str]
    call_status: Optional[str]
    disconnection_reason: Optional[str]

    from_number: Optional[str]
    to_number: Optional[str]

    start_timestamp: Optional[datetime]
    end_timestamp: Optional[datetime]

    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    retell_llm_dynamic_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    collected_dynamic_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)

    recording_url: Optional[str]
    recording_multi_channel_url: Optional[str]
    scrubbed_recording_url: Optional[str]
    scrubbed_recording_multi_channel_url: Optional[str]
    public_log_url: Optional[str]
    knowledge_base_retrieved_contents_url: Optional[str]

    transcript: Optional[str]
    transcript_object: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    transcript_with_tool_calls: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    scrubbed_transcript_with_tool_calls: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    llm_token_usage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


