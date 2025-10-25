from math import ceil
from uuid import UUID
from fastapi import (
    APIRouter, 
    status, 
    Query,
    Depends, 
)
from beanie.operators import RegEx
from app.core.exceptions.base import (
    AppException,
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
    CampaignModel,
    CampaignContactsModel,
)
from .schemas import (
    APIBaseResponse,
    PaginationMeta,
    PaginaionResponse,
    
    CampaignCreatePayloadSchema,
    CampaignFilterParams,
    CampaignModifyPayloadSchema,
    
    CampaignContactCreatePayloadSchema,
    CampaignContactFilterParams,
    CampaignContactResponseSchema,
    CampaignContactModifyPayloadSchema,

    CampaignInfoSchema,
)
from app.config.logger import get_logger


logger = get_logger("Campaign Routes")

campaign_router = APIRouter()


#### Campaign ####

@campaign_router.post(
    "/create",
    response_model=APIBaseResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_campaign(
    payload: CampaignCreatePayloadSchema,
    user : UserModel = Depends(ProfileActive())
):
    agent = await AgentModel.find_one(
        AgentModel.id == payload.agent_uid,
        AgentModel.user.id == user.id
    )
    if not agent:
        raise NotFoundException("Agent not found")

    campaign = CampaignModel(
        user=user,
        agent=agent,
        name=payload.name
    )
    await campaign.insert()

    return APIBaseResponse(
        status=True,
        message="Campaign created successfully",
        data=CampaignInfoSchema.model_validate(campaign) 
    )


@campaign_router.get(
    "/list",
    response_model=PaginaionResponse,
    status_code=status.HTTP_200_OK,
)
async def retrieve_my_campaigns(
    user: UserModel = Depends(ProfileActive()),
    filters: CampaignFilterParams = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    skip = (page - 1) * page_size

    filter_conditions = [
        CampaignModel.user.id == user.id
    ]

    if filters.id:
        filter_conditions.append(CampaignModel.id == filters.id)
    if filters.agent_id:
        filter_conditions.append(CampaignModel.agent.id == filters.agent_id)
    if filters.name:
        filter_conditions.append(RegEx(CampaignModel.name, f".*{filters.name}.*", options="i"))
    if filters.is_deleted is not None:
        filter_conditions.append(CampaignModel.is_deleted == filters.is_deleted)
    else:
        filter_conditions.append(CampaignModel.is_deleted == False)

    total_records = await CampaignModel.find(*filter_conditions).count()

    all_campaigns = (
        await CampaignModel.find(*filter_conditions, fetch_links=True)
        .sort(-CampaignModel.created_at)
        .skip(skip)
        .limit(page_size)
        .to_list()
    )

    serialized_campaigns = [
        CampaignInfoSchema.model_validate(campaign) for campaign in all_campaigns
    ]

    # Calculate pagination flags
    total_pages = ceil(total_records / page_size)
    is_next = page < total_pages
    is_previous = page > 1

    return PaginaionResponse(
        status = True,
        message = "All campaigns retrieved successfully",
        meta = PaginationMeta(
            page_size = page_size,
            page = page,
            total_records = total_records,
            total_pages = total_pages,
            is_next = is_next,
            is_previous = is_previous,
        ),
        data = serialized_campaigns
    )


@campaign_router.patch(
    "/modify",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def modify_campaign(
    payload : CampaignModifyPayloadSchema,
    user : UserModel = Depends(dependency=ProfileActive())
):
    campaign = await CampaignModel.find_one(
        CampaignModel.id == payload.campaign_uid,
        CampaignModel.user.id == user.id,
        fetch_links=True
    )
    if not campaign:
        raise NotFoundException("Campaign not found")
    
    update_data = {}

    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop("campaign_uid", None)
    update_data.pop("agent_uid", None)

    if payload.agent_uid:
        agent = await AgentModel.find_one(
            AgentModel.id == payload.agent_uid,
            AgentModel.user.id == user.id
        )
        if not agent:
            raise NotFoundException("Agent not found")
        update_data["agent"] = agent

    if update_data:
        for key, value in update_data.items():
            setattr(campaign, key, value)
        await campaign.save()
    
    return APIBaseResponse(
        status=True,
        message="Campaign updated successfully",
        data=CampaignInfoSchema.model_validate(campaign) 
    )



@campaign_router.delete(
    "/delete",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def delete_campaign(
    campaign_uid: UUID = Query(..., description="Campaign UUID to delete"),
    user : UserModel = Depends(dependency=ProfileActive())
):
    campaign = await CampaignModel.find_one(
        CampaignModel.id == campaign_uid,
        CampaignModel.user.id == user.id,
        CampaignModel.is_deleted == False
    )
    if not campaign:
        raise NotFoundException("Campaign not found")

    campaign_contacts = await CampaignContactsModel.find(
        CampaignContactsModel.campaign.id == campaign_uid
    ).count()
    if campaign_contacts > 0:
        raise AppException(
            "Contacts already exist in this campaign. Please delete all contacts first."
        )

    await campaign.set({"is_deleted": True})

    return APIBaseResponse(
        status=True,
        message="Campaign deleted successfully"
    )


#### Campaign Contact ####

@campaign_router.post(
    "/contact/create",
    response_model=APIBaseResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_campaign_contact(
    payload: CampaignContactCreatePayloadSchema,
    user : UserModel = Depends(ProfileActive())
):
    # find and verify campaign aligns with same user
    campaign = await CampaignModel.find_one(
        CampaignModel.id == payload.campaign_uid,
        CampaignModel.user.id == user.id
    )
    if not campaign:
        raise NotFoundException("Campaign not found")
    
    # check if contact already exists in same campaign
    if await CampaignContactsModel.find(
        CampaignContactsModel.phone_number == payload.phone_number
    ).count() > 0:
        raise AppException("This phone Number already exists in this campaign")

    data = payload.dict(exclude={"campaign_uid"})
    campaign_contact = CampaignContactsModel(
        user=user,
        campaign=campaign,
        **data
    )
    await campaign_contact.insert()

    return APIBaseResponse(
        status=True,
        message="Campaign's contact created successfully",
        data=CampaignContactResponseSchema.model_validate(campaign_contact) 
    )


@campaign_router.get(
    "/contact/list",
    response_model=PaginaionResponse,
    status_code=status.HTTP_200_OK,
)
async def retrieve_my_campaigns_contacts(
    user: UserModel = Depends(ProfileActive()),
    filters: CampaignContactFilterParams = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    skip = (page - 1) * page_size

    filter_conditions = [
        CampaignContactsModel.user.id == user.id
    ]

    if filters.id:
        filter_conditions.append(CampaignContactsModel.id == filters.id)
    if filters.campaign_id:
        filter_conditions.append(CampaignContactsModel.campaign.id == filters.campaign_id)
    if filters.phone_number:
        filter_conditions.append(RegEx(CampaignContactsModel.phone_number, f".*{filters.phone_number}.*", options="i"))
    if filters.first_name:
        filter_conditions.append(RegEx(CampaignContactsModel.first_name, f".*{filters.first_name}.*", options="i"))
    if filters.last_name:
        filter_conditions.append(RegEx(CampaignContactsModel.last_name, f".*{filters.last_name}.*", options="i"))
    if filters.email:
        filter_conditions.append(RegEx(CampaignContactsModel.email, f".*{filters.email}.*", options="i"))

    total_records = await CampaignContactsModel.find(*filter_conditions).count()

    all_campaigns_contacts = (
        await CampaignContactsModel.find(*filter_conditions, fetch_links=True)
        .sort(-CampaignContactsModel.created_at)
        .skip(skip)
        .limit(page_size)
        .to_list()
    )

    serialized_campaigns_contacts = [
        CampaignContactResponseSchema.model_validate(campaign_contact) for campaign_contact in all_campaigns_contacts
    ]

    # Calculate pagination flags
    total_pages = ceil(total_records / page_size)
    is_next = page < total_pages
    is_previous = page > 1

    return PaginaionResponse(
        status = True,
        message = "All campaigns retrieved successfully",
        meta = PaginationMeta(
            page_size = page_size,
            page = page,
            total_records = total_records,
            total_pages = total_pages,
            is_next = is_next,
            is_previous = is_previous,
        ),
        data = serialized_campaigns_contacts
    )


@campaign_router.patch(
    "/contact/modify",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def modify_campaign_contact(
    payload : CampaignContactModifyPayloadSchema,
    user : UserModel = Depends(dependency=ProfileActive())
):
    campaign_contact = await CampaignContactsModel.find_one(
        CampaignContactsModel.id == payload.campaign_contact_uid,
        CampaignContactsModel.user.id == user.id,
        fetch_links=True
    )
    if not campaign_contact:
        raise NotFoundException("Campaign contact not found")
    
    # exclude_unset=True → ignore keys not present in payload
    update_data = payload.model_dump(exclude_unset=True)
    # update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    update_data.pop("campaign_contact_uid", None)

    # Step 3: Perform dynamic update only for provided fields
    if update_data:
        await campaign_contact.set(update_data)

    return APIBaseResponse(
        status=True,
        message="Campaign contact updated successfully",
        data=CampaignContactResponseSchema.model_validate(campaign_contact)
    )


@campaign_router.delete(
    "/contact/delete",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK
)
async def delete_campaign_contact(
    campaign_contact_uid : UUID = Query(description= "Campaign's contact uuid"),
    user : UserModel = Depends(dependency=ProfileActive())
):
    campaign_contact : CampaignContactsModel = await CampaignContactsModel.find_one(
        CampaignContactsModel.id == campaign_contact_uid,
        CampaignContactsModel.user.id == user.id
    )
    if not campaign_contact:
        raise NotFoundException("Campaign's Contact not found")

    if campaign_contact.no_of_calls > 0:
        raise AppException("Cannot delete contact because a conversation has already started")

    await campaign_contact.delete()
    return APIBaseResponse(
        status=True,
        message="Campaign contact deleted successfully",
    )


