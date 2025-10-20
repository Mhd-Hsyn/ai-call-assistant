from uuid import UUID
from datetime import datetime
from pydantic import (
    BaseModel,
    ValidationInfo,
    Field, 
    field_validator
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


