from fastapi import (
    APIRouter, 
    Request, 
    status, 
    UploadFile, 
    Body, 
    Depends, 
)
from app.config.settings import settings
from app.core.exceptions.base import (
    AppException,
    InternalServerErrorException,
    ToManyRequestExeption,
    NotFoundException,
)
from app.core.dependencies.authentication import (
    JWTAuthentication
)
from app.core.dependencies.authorization import (
    EmailVerified, 
    ProfileActive
)
from app.core.constants.choices import (
    KnowledgeBaseStatusChoices,
    KnowledgeBaseSourceTypeChoices
)
from ..models import (
    KnowledgeBaseModel,
    KnowledgeBaseSourceModel
)
from app.core.utils.save_images import (
    save_profile_image
)
knowledge_base_router = APIRouter()
