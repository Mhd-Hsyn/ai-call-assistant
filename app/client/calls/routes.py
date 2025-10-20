from uuid import UUID
from typing import Optional
from beanie.operators import In
from fastapi import (
    APIRouter, 
    status, 
    Query, 
    Depends, 
)
from app.config.settings import settings
from app.core.exceptions.base import (
    BadGatewayException,
    NotFoundException

)
from app.core.dependencies.authorization import (
    ProfileActive
)
from app.auth.models import (
    UserModel
)
from ..models import (
    AgentModel,
    CallModel
)
from .schemas import (
    APIBaseResponse,

)
# from .services import (
    
# )
from app.config.logger import get_logger


logger = get_logger("Calling Routes")

calls_router = APIRouter()


