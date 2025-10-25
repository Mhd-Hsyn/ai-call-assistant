from math import ceil
from uuid import UUID
from decimal import Decimal
from fastapi import (
    APIRouter, 
    status, 
    UploadFile,
    Query,
    File,
    Depends, 
)
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
    CallModel,
    AgentModel,
    CampaignModel,
    CampaignContactsModel,
)
from .schemas import (
    APIBaseResponse,
    PaginationMeta,
    PaginaionResponse,
    CampaignCreatePayloadSchema,
    CampaignModifyPayloadSchema,
    CampaignInfoSchema,
    CallInitializeSchema,
    CallDisplayInfoResponseSchema,
    CallFullResponseSchema,
)
from .services import (
    RetellCallService,
    CallFileService,
    RetellWebhookService,
)
from app.config.logger import get_logger


logger = get_logger("Calling Routes")

calls_router = APIRouter()


@calls_router.post(
    "/campaign/create",
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


@calls_router.get(
    "/campaign/list",
    response_model=PaginaionResponse,
    status_code=status.HTTP_200_OK,
)
async def retrieve_my_campaigns(
    user: UserModel = Depends(ProfileActive()),
    page: int = 1,
    page_size: int = 10,
):
    skip = (page - 1) * page_size
    total_records = await CampaignModel.find(
        CampaignModel.user.id == user.id,
        CampaignModel.is_deleted == False
    ).count()

    all_campaigns = (
        await CampaignModel.find(
            CampaignModel.user.id == user.id,
            CampaignModel.is_deleted == False,
            fetch_links=True
        )
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


@calls_router.patch(
    "/campaign/modify",
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
    
    update_fields = {}

    if payload.name and payload.name != campaign.name:
        update_fields["name"] = payload.name
    if payload.agent_uid:
        agent = await AgentModel.find_one(
            AgentModel.id == payload.agent_uid,
            AgentModel.user.id == user.id
        )
        if not agent:
            raise NotFoundException("Agent not found")
        update_fields["agent"] = agent

    if update_fields:
        for key, value in update_fields.items():
            setattr(campaign, key, value)
        await campaign.save()
    
    return APIBaseResponse(
        status=True,
        message="Campaign updated successfully",
        data=CampaignInfoSchema.model_validate(campaign) 
    )



@calls_router.patch(
    "/campaign/delete",
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
        CampaignContactsModel.campaign == campaign
    ).count()
    if campaign_contacts > 0:
        raise AppException("Contacts already exist in this campaign. Please delete all contacts first.")

    await campaign.set({"is_deleted": True})

    return APIBaseResponse(
        status=True,
        message="Campaign deleted successfully"
    )





@calls_router.post(
    "/parse-file",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def parse_file(file: UploadFile = File(...)):
    """
    Upload Excel or CSV file → Get array of key-value objects
    """
    records = await CallFileService.parse_uploaded_file(file)
    return APIBaseResponse(
        status=True,
        message="File parsed successfully",
        data=records
    )



@calls_router.post(
    "/initialize-call",
    response_model=APIBaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initialize_call(
    payload: CallInitializeSchema,
    user: UserModel = Depends(ProfileActive()),
):
    """
    Initialize a phone call through Retell and store it in DB.
    """
    service = RetellCallService()
    new_call = await service.create_phone_call(user=user, payload=payload.dict(by_alias=True))

    return APIBaseResponse(
        status=True,
        message="Call initialized successfully",
        data={
            "call_id": new_call.call_id, 
            "agent_id": new_call.agent_retell_id
        }
    )



# {{BASE_URL}}/api/clientside/calls/retell/webhook
@calls_router.post("/retell/webhook")
async def retell_webhook(payload: dict):
    """
    Handles Retell call lifecycle webhooks.
    """
    try:
        service = RetellWebhookService()
        return await service.handle_event(payload)
    except Exception as e:
        raise AppException(str(e))



@calls_router.get(
    "/list",
    response_model=PaginaionResponse,
    status_code=status.HTTP_200_OK,
)
async def retrieve_my_calls(
    user: UserModel = Depends(ProfileActive()),
    page: int = 1,
    page_size: int = 10,
):
    skip = (page - 1) * page_size
    total_records = await CallModel.find(CallModel.user.id == user.id).count()

    all_calls = (
        await CallModel.find(
            CallModel.user.id == user.id
        )
        .sort(-CallModel.created_at)
        .skip(skip)
        .limit(page_size)
        .to_list()
    )

    serialized_calls = [
        CallDisplayInfoResponseSchema.model_validate(call) for call in all_calls
    ]

    # Calculate pagination flags
    total_pages = ceil(total_records / page_size)
    is_next = page < total_pages
    is_previous = page > 1

    return PaginaionResponse(
        status=True,
        message="All calls retrieved successfully",
        meta = PaginationMeta(
            page_size = page_size,
            page = page,
            total_records = total_records,
            total_pages = total_pages,
            is_next = is_next,
            is_previous = is_previous,
        ),
        data= serialized_calls
    )


@calls_router.get(
    "/detail",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def retrieve_my_calls(
    user: UserModel = Depends(ProfileActive()),
    call_uuid : UUID = Query(..., description="call uuid")
):
    call = await CallModel.find_one(
        CallModel.id == call_uuid,
        CallModel.user.id == user.id,
        fetch_links=True 
    )

    serialized_calls = CallFullResponseSchema.model_validate(call)

    return APIBaseResponse(
        status=True,
        message="call details retrieved successfully",
        data=serialized_calls,
    )


@calls_router.post(
    "/sync-call-fields",
    status_code=status.HTTP_200_OK,
    response_model=APIBaseResponse,
    summary="🔄 Sync call_analysis & call_cost fields into separate model fields",
)
async def sync_call_fields():
    """
    Scans all calls in DB and extracts:
      - From call_analysis → user_sentiment, call_successful
      - From call_cost → combined_cost, total_duration, total_duration_unit_price
    Updates them in the database.
    """

    updated_count = 0
    skipped_count = 0

    all_calls = await CallModel.find_all().to_list()

    for call in all_calls:
        try:
            # --- Extract from call_analysis ---
            analysis = call.call_analysis or {}
            user_sentiment = analysis.get("user_sentiment")
            call_successful = analysis.get("call_successful")

            # --- Extract from call_cost ---
            cost = call.call_cost or {}
            combined_cost = Decimal(str(cost.get("combined_cost", 0)))
            total_duration = cost.get("total_duration_seconds", 0)
            total_duration_unit_price = Decimal(str(cost.get("total_duration_unit_price", 0)))

            # --- Only update if any field exists ---
            if any([
                user_sentiment,
                call_successful is not None,
                combined_cost != 0,
                total_duration,
                total_duration_unit_price != 0,
            ]):
                call.user_sentiment = user_sentiment
                call.call_successful = call_successful
                call.combined_cost = combined_cost
                call.total_duration = total_duration
                call.total_duration_unit_price = total_duration_unit_price
                await call.save()
                updated_count += 1
            else:
                skipped_count += 1

        except Exception as e:
            print(f"❌ Error updating call {call.call_id}: {e}")
            skipped_count += 1

    return APIBaseResponse(
        status=True,
        message="Call fields synced successfully",
        data={
            "total_calls": len(all_calls),
            "updated": updated_count,
            "skipped": skipped_count,
        },
    )


