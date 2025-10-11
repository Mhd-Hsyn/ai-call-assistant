from uuid import UUID
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
from .service import (
    RetellKnowledgeBaseService,
    RetellService,

)
from .schemas import (
    APIBaseResponse,
    KnowledgeBaseCreateForm,
    KnowledgeBaseResponse,
    SitemapRequest,
    KnowledgeBaseDetailResponse,
    KnowledgeBaseSourceResponse

)


knowledge_base_router = APIRouter()


@knowledge_base_router.post(
    "/list-sitemap", 
    response_model=APIBaseResponse, 
    status_code=status.HTTP_200_OK
)
async def list_sitemap(payload: SitemapRequest):
    """
    🌐 Fetch sitemap links from Retell AI API (via service layer).
    """
    sitemap_data = await RetellService.list_sitemap(payload.website_url)

    return APIBaseResponse(
        status=True,
        message="Sitemap fetched successfully",
        data=sitemap_data
    )




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



@knowledge_base_router.get(
    "/{knowledge_base_uuid}",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def get_knowledge_base(
    knowledge_base_uuid: UUID,
    user: UserModel = Depends(ProfileActive()),
):
    """
    📚 Get a Knowledge Base and its associated Sources.
    Only accessible to the owner (authenticated user).
    """

    # ✅ Fetch knowledge base for this user
    kb = await KnowledgeBaseModel.find_one(
        KnowledgeBaseModel.id == knowledge_base_uuid,
        KnowledgeBaseModel.user.id == user.id,
    )

    if not kb:
        raise NotFoundException("Knowledge base not found")

    # ✅ Fetch all related sources
    sources = await KnowledgeBaseSourceModel.find(
        KnowledgeBaseSourceModel.knowledge_base.id == kb.id
    ).to_list()

    # ✅ Serialize sources
    source_responses = [
        KnowledgeBaseSourceResponse.model_validate(s) for s in sources
    ]

    # ✅ Build final knowledge base response
    kb_response = KnowledgeBaseDetailResponse(
        **kb.model_dump(),
        sources=source_responses,
    )

    return APIBaseResponse(
        status=True,
        message="Knowledge base fetched successfully",
        data=kb_response,
    )


