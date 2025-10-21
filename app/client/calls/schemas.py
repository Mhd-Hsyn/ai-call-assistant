from uuid import UUID
from datetime import datetime
from pydantic import (
    BaseModel,
    Field, 
)
from typing import (
    List, 
    Optional, 
    Dict,
    Any
)
from app.core.constants.choices import (
    CallDirectionChoices,
    CallStatusChoices,
    CallTypeChoices
)


class APIBaseResponse(BaseModel):
    status: bool
    message: str
    data: Any | None = None



class CallInitializeSchema(BaseModel):
    from_number: str
    to_number: str
    override_agent_id: Optional[str] = Field(None, alias="override_agent_id")
    retell_llm_dynamic_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)



class CallResponseSchema(BaseModel):
    id : UUID
    call_id: str
    agent_name: Optional[str]
    agent_retell_id: Optional[str]
    call_type: Optional[str]
    direction: Optional[str]
    call_status: Optional[str]
    disconnection_reason: Optional[str]

    from_number: Optional[str]
    to_number: Optional[str]

    start_timestamp: Optional[datetime]
    end_timestamp: Optional[datetime]
    duration_ms: Optional[int]

    recording_url: Optional[str]
    public_log_url: Optional[str]
    transcript: Optional[str]

    call_analysis: Optional[Dict[str, Any]] = None
    call_cost: Optional[Dict[str, Any]] = None
    llm_token_usage: Optional[Dict[str, Any]] = None

    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p") if isinstance(v, datetime) else v,
        }


