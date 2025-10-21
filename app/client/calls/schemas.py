from uuid import UUID
from datetime import datetime
from pydantic import (
    BaseModel,
    Field, 
    computed_field,
)
from typing import (
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



class CallDisplayInfoResponseSchema(BaseModel):
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

    duration_ms: Optional[int]

    call_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    call_cost: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # 🧠 Derived (computed) fields
    @computed_field(return_type=str)
    def formatted_duration(self) -> Optional[str]:
        """Convert duration from milliseconds → HH:MM:SS format"""
        if not self.duration_ms:
            return None
        total_seconds = int(self.duration_ms / 1000)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @computed_field(return_type=str)
    def user_sentiment(self) -> Optional[str]:
        """Extract user sentiment from call_analysis"""
        if self.call_analysis and "user_sentiment" in self.call_analysis:
            return self.call_analysis["user_sentiment"]
        return None

    @computed_field(return_type=float)
    def total_cost_usd(self) -> Optional[float]:
        """
        Convert combined_cost (in cents) → USD (rounded to 2 decimal places)
        If 'combined_cost' already in USD, adjust as needed.
        """
        if self.call_cost and "combined_cost" in self.call_cost:
            # Assuming backend stores cost in cents → divide by 100
            cost_cents = self.call_cost["combined_cost"]
            return round(cost_cents / 100, 2)
        return None

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p") if isinstance(v, datetime) else v,
        }


