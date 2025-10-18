from uuid import UUID
from typing import List
from collections import defaultdict
from beanie.operators import In
from fastapi import (
    APIRouter, 
    status, 
    Query,
    Depends, 
)
from app.core.exceptions.base import (
    NotFoundException,
    ForbiddenException,
)
from app.core.dependencies.authorization import (
    ProfileActive
)
from app.core.constants.choices import (
    KnowledgeBaseStatusChoices,
)
from ..models import (
    KnowledgeBaseModel,
    KnowledgeBaseSourceModel
)
from app.auth.models import (
    UserModel
)
from .service import (
    RetellKnowledgeBaseService,
    RetellService,

)
from .sync_service import (
    RetellSyncService
)
from .schemas import (
    APIBaseResponse,
    KnowledgeBaseCreateForm,
    KnowledgeBaseResponse,
    SitemapRequest,
    KnowledgeBaseDetailResponse,
    KnowledgeBaseSourceResponse,
    KnowledgeBaseInfoResponse

)
from app.config.logger import get_logger

logger = get_logger("Knowledge Base route")

knowledge_base_router = APIRouter()


@knowledge_base_router.post(
    "/list-sitemap", 
    response_model=APIBaseResponse, 
    status_code=status.HTTP_200_OK
)
async def list_sitemap(payload: SitemapRequest):
    """
    Fetch sitemap links from Retell AI API (via service layer).
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
    Create a Knowledge Base (Texts + URLs + Files)
    """
    response = await RetellKnowledgeBaseService.create_knowledge_base(
        name=payload.name,
        texts=payload.texts,
        urls=payload.urls,
        files=payload.files,
    )

    # Save locally
    kb = KnowledgeBaseModel(
        user=user,
        knowledge_base_id=response.knowledge_base_id,
        name=payload.name,
        status=KnowledgeBaseStatusChoices.IN_PROGRESS,
    )
    await kb.insert()

    data = KnowledgeBaseResponse.model_validate(kb)
    return APIBaseResponse(
        status=True,
        message="Knowledge base created successfully",
        data=data
    )


@knowledge_base_router.get("/list-detail")
async def list_user_knowledge_bases(user: UserModel = Depends(ProfileActive())):
    knowledge_bases = (
        await KnowledgeBaseModel.find(
            KnowledgeBaseModel.user.id == user.id
        )
        .sort(-KnowledgeBaseModel.created_at)
        .to_list()
    )

    if not knowledge_bases:
        return APIBaseResponse(status=True, message="No knowledge bases found", data=[])

    kb_ids = [kb.id for kb in knowledge_bases]
    sources = (
        await KnowledgeBaseSourceModel.find(
            In("knowledge_base.$id", kb_ids)
        )
        .sort(-KnowledgeBaseSourceModel.created_at)
        .to_list()
    )

    # Group efficiently
    sources_by_kb = defaultdict(list)
    for s in sources:
        sources_by_kb[s.knowledge_base.ref.id].append(s)

    # Build response using list comprehension (fast)
    kb_responses = [
        KnowledgeBaseDetailResponse(
            **kb.model_dump(),
            sources=[KnowledgeBaseSourceResponse(**s.model_dump()) for s in sources_by_kb.get(kb.id, [])],
        )
        for kb in knowledge_bases
    ]

    return APIBaseResponse(
        status=True,
        message="Knowledge bases fetched successfully",
        data=kb_responses,
    )


@knowledge_base_router.get(
    "/retrieve-detail",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def get_knowledge_base_with_sources(
    knowledge_base_uuid: UUID = Query(..., description="Knowledge base UUID"),
    user: UserModel = Depends(ProfileActive()),
):
    """
    Get a single Knowledge Base and its associated Sources.
    Accessible only to the authenticated owner.
    """

    # Fetch KB for this user
    kb = await KnowledgeBaseModel.find_one(
        KnowledgeBaseModel.id == knowledge_base_uuid,
        KnowledgeBaseModel.user.id == user.id,
    )

    if not kb:
        raise NotFoundException("Knowledge base not found")

    # Fetch all related sources
    sources = await KnowledgeBaseSourceModel.find(
        KnowledgeBaseSourceModel.knowledge_base.id == kb.id
    ).sort(-KnowledgeBaseSourceModel.created_at).to_list()

    # Serialize sources
    source_responses = [
        KnowledgeBaseSourceResponse.model_validate(s) for s in sources
    ]

    # Build final KB response
    kb_response = KnowledgeBaseDetailResponse(
        **kb.model_dump(),
        sources=source_responses,
    )

    return APIBaseResponse(
        status=True,
        message="Knowledge base fetched successfully (with sources)",
        data=kb_response,
    )


@knowledge_base_router.get(
    "/list-info",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def list_user_knowledge_bases_only(
    user: UserModel = Depends(ProfileActive())
):
    """
    Get all knowledge bases for current user (without sources).
    Returns lightweight info: id, name, status, created_at, updated_at
    """

    # Fetch all KBs for this user
    knowledge_bases = (
        await KnowledgeBaseModel.find(
            KnowledgeBaseModel.user.id == user.id
        )
        .sort(-KnowledgeBaseModel.created_at)
        .to_list()
    )

    if not knowledge_bases:
        return APIBaseResponse(
            status=True,
            message="No knowledge bases found",
            data=[],
        )

    # Use response schema for clean serialization
    kb_responses: List[KnowledgeBaseInfoResponse] = [
        KnowledgeBaseInfoResponse.model_validate(kb) for kb in knowledge_bases
    ]

    return APIBaseResponse(
        status=True,
        message="Knowledge bases fetched successfully (without sources)",
        data=kb_responses,
    )


@knowledge_base_router.delete(
    path="/delete-source",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_source(
    user: UserModel = Depends(ProfileActive()),
    source_uuid: UUID = Query(..., description="Knowledge Base Source UUID"),
    knowledgebase_uuid: UUID = Query(..., description="Knowledge Base UUID"),
):
    # Verify KB belongs to user (single optimized query)
    kb = await KnowledgeBaseModel.find_one(
        KnowledgeBaseModel.id == knowledgebase_uuid,
        KnowledgeBaseModel.user.id == user.id,
    )

    if not kb:
        raise ForbiddenException("You are not authorized to delete this source or KB not found.")

    # Fetch the source ensuring it's linked to this KB
    source = await KnowledgeBaseSourceModel.find_one(
        KnowledgeBaseSourceModel.id == source_uuid,
        KnowledgeBaseSourceModel.knowledge_base.id == kb.id
    )

    if not source:
        raise NotFoundException("Source not found in this Knowledge Base.")

    # Delete from Retell (external sync)
    await RetellKnowledgeBaseService.delete_source_from_retell(
        source_id=source.source_id,
        knowledge_base_id=kb.knowledge_base_id
    )

    # Delete locally
    await source.delete()

    return APIBaseResponse(
        status=True,
        message="Source deleted successfully",
        data=None,
    )


@knowledge_base_router.delete(
    path='/delete-knowledgebase',
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def delete_source(
    user: UserModel = Depends(dependency=ProfileActive()),
    knowledgebase_uuid: UUID = Query(..., description="Knowledge Base Source UUID"),
):

    knowledgebase = await KnowledgeBaseModel.get(str(knowledgebase_uuid), fetch_links=True)

    if not knowledgebase:
        raise NotFoundException("Knowledge Base not found.")

    await knowledgebase.fetch_link(KnowledgeBaseModel.user)

    if knowledgebase.user.id != user.id:
        raise ForbiddenException("You are not authorized to delete this source.")

    await RetellKnowledgeBaseService.delete_knowledge_base_from_retell(
        knowledge_base_id=knowledgebase.knowledge_base_id
    )

    # Delete the source
    await knowledgebase.delete()

    return APIBaseResponse(
        status=True,
        message="Source deleted successfully",
        data=None
    )





@knowledge_base_router.post(
    "/retell/sync-user",
    status_code=status.HTTP_200_OK,
    response_model=APIBaseResponse,
)
async def sync_user_knowledge_bases_from_retell(
    user: UserModel = Depends(ProfileActive()),
):
    """
    Sync all IN_PROGRESS knowledge bases for the current user with Retell API.
    - Fetches latest KB data from Retell
    - Adds missing sources
    - Updates KB status if changed
    """
    result = await RetellSyncService.sync_user_knowledge_bases(user)

    return APIBaseResponse(
        status=True,
        message="User knowledge bases synced successfully",
        data=result,
    )


@knowledge_base_router.post("/retell/sync-all", status_code=status.HTTP_200_OK, response_model=APIBaseResponse)
async def sync_knowledge_bases_from_retell():
    """
    Sync all IN_PROGRESS knowledge bases with Retell API.
    - Fetches latest data
    - Adds missing sources
    - Updates KB status if changed
    """
    result = await RetellSyncService.sync_in_progress_knowledge_bases()

    return APIBaseResponse(
        status=True,
        message="Knowledge bases synced successfully",
        data=result,
    )





