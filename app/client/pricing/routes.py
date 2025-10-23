from math import ceil
from fastapi import (
    APIRouter, 
    status, 
    Depends, 
)
from app.core.exceptions.base import (
    AppException,
)
from app.core.dependencies.authorization import (
    ProfileActive
)
from app.auth.models import (
    UserModel
)
from ..models import (
    CallModel
)
from .schemas import (
    APIBaseResponse,
    PaginaionResponse,
    PaginationMeta,
    CallPriceResponseSchema,

)
from app.core.utils.helpers import (
    format_seconds_duration
)
from app.config.logger import get_logger

logger = get_logger('Pricing route')

pricing_router = APIRouter()



@pricing_router.get(
    "/calls",
    response_model=PaginaionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get paginated list of user's calls"
)
async def list_user_calls(
    user: UserModel = Depends(ProfileActive()),
    page: int = 1,
    page_size: int = 10,
):
    skip = (page - 1) * page_size
    total_records = await CallModel.find(CallModel.user.id == user.id).count()

    calls = (
        await CallModel.find(CallModel.user.id == user.id)
        .sort(-CallModel.created_at)
        .skip(skip)
        .limit(page_size)
        .to_list()
    )

    serialized = [CallPriceResponseSchema.model_validate(c) for c in calls]

    # Calculate pagination flags
    total_pages = ceil(total_records / page_size)
    is_next = page < total_pages
    is_previous = page > 1

    return PaginaionResponse(
        status=True,
        message="Fetched call list successfully",
        meta = PaginationMeta(
            page_size = page_size,
            page = page,
            total_records = total_records,
            total_pages = total_pages,
            is_next = is_next,
            is_previous = is_previous,
        ),
        data= serialized
    )



@pricing_router.get(
    "/call-summary",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get total call cost summary for current user"
)
async def get_call_summary(user: UserModel = Depends(ProfileActive())):
    pipeline = [
        {"$match": {"user.$id": user.id}},
        {"$group": {
            "_id": None, 
            "total_cents": {"$sum": "$call_cost.combined_cost"},
            "total_duration_seconds": {"$sum": "$call_cost.total_duration_seconds"}
        }}
    ]
    summary = await CallModel.aggregate(pipeline).to_list()
    total_cents = summary[0]["total_cents"] if summary else 0
    total_usd = round(total_cents / 100, 2)

    total_duration_seconds = summary[0]["total_duration_seconds"] if summary else 0

    return APIBaseResponse(
        status=True,
        message="Call cost summary fetched successfully",
        data={
            "total_duration_seconds": total_duration_seconds,
            "formatted_durations": format_seconds_duration(total_duration_seconds),
            "total_cost_usd": total_usd, 
            "total_cost_cents": total_cents
        }
    )





