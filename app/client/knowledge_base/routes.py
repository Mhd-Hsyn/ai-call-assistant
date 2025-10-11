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
from app.auth.models import (
    UserModel
)
from app.core.utils.save_images import (
    save_profile_image
)
from .schemas import (
    APIBaseResponse,
    KnowledgeBaseCreateForm,
    KnowledgeBaseResponse,

)
from .service import (
    RetellKnowledgeBaseService
)


knowledge_base_router = APIRouter()




@knowledge_base_router.post(
    "/create",
    response_model=APIBaseResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_knowledge_base(
    payload: KnowledgeBaseCreateForm = Depends(),
    user: UserModel = Depends(ProfileActive())
):
    """
    🧠 Create Knowledge Base
    """

    # Upload file bytes if available
    file_bytes = [await f.read() for f in (payload.files or [])] if payload.files else None

    # Create on Retell
    knowledge_base_response = RetellKnowledgeBaseService.create_knowledge_base(
        name=payload.name,
        texts=payload.texts,
        urls=payload.urls,
        files=file_bytes,
    )

    # Save to DB
    kb = KnowledgeBaseModel(
        user=user,
        knowledge_base_id=knowledge_base_response.knowledge_base_id,
        name=payload.name,
        status=KnowledgeBaseStatusChoices.IN_PROGRESS,
    )
    await kb.insert()

    data = KnowledgeBaseResponse.model_validate(kb)

    return APIBaseResponse(
        status=True,
        message="Knowledge base created successfully",
        data= data
    )

