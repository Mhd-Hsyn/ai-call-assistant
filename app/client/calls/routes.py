import json
from uuid import UUID
from datetime import datetime
from fastapi import (
    APIRouter, 
    status, 
    UploadFile,
    Query,
    File,
    Depends, 
)
from app.config.settings import settings
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
    CallModel
)
from .schemas import (
    APIBaseResponse,
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
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def retrieve_my_calls(user: UserModel = Depends(ProfileActive())):
    all_calls = (
        await CallModel.find(
            CallModel.user.id == user.id
        )
        .sort(-CallModel.created_at)
        .to_list()
    )

    serialized_calls = [
        CallDisplayInfoResponseSchema.model_validate(call) for call in all_calls
    ]

    return APIBaseResponse(
        status=True,
        message="All calls retrieved successfully",
        data=serialized_calls,
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




