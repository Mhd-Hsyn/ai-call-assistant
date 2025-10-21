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



