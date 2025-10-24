from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import (
    BaseModel,
    Field,
    computed_field,
)
from typing import (
    List,
    Optional, 
    Dict,
    Any
)
from app.core.utils.helpers import (
    format_milliseconds_duration,
    convert_cents_to_usd,

)

class APIBaseResponse(BaseModel):
    status: bool
    message: str
    data: Any | None = None


class PaginationMeta(BaseModel):
    page_size: int
    page: int
    total_records: int
    total_pages: int
    is_next: bool
    is_previous: bool

class PaginaionResponse(BaseModel):
    status: bool
    message: str
    meta : PaginationMeta
    data: Any | None = None




class CallPriceResponseSchema(BaseModel):
    id: UUID
    call_id: str

    agent_name: Optional[str]
    direction: Optional[str]
    call_status: Optional[str]
    disconnection_reason: Optional[str]

    from_number: Optional[str]
    to_number: Optional[str]

    start_timestamp: Optional[datetime]
    end_timestamp: Optional[datetime]

    duration_ms: Optional[int]
    call_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    call_cost: Optional[Dict[str, Any]] = Field(default_factory=dict)

    user_sentiment : Optional[str]
    call_successful : Optional[bool]
    combined_cost : Optional[Decimal]

    @computed_field(return_type=str)
    def formatted_duration(self) -> Optional[str]:
        if not self.duration_ms:
            return None
        return format_milliseconds_duration(self.duration_ms)

    @computed_field(return_type=Decimal)
    def total_cost_usd(self) -> Optional[Decimal]:
        if self.combined_cost:
            return convert_cents_to_usd(self.combined_cost)
        return None

    @computed_field(return_type=List[Dict[str, Any]])
    def product_costs_usd(self) -> Optional[List[Dict[str, Any]]]:
        """
        ✅ Convert each product cost in cents to USD and calculate per-minute USD rate.
        Keeps structure, includes cost_usd, unit_price_usd, and per_minute_usd.
        """
        if not self.call_cost or "product_costs" not in self.call_cost:
            return None

        total_duration_seconds = self.call_cost.get("total_duration_seconds", 0)
        total_minutes = total_duration_seconds / 60 if total_duration_seconds else 0

        converted_products = []

        for product in self.call_cost["product_costs"]:
            product_name = product.get("product")
            unit_price_cents = product.get("unit_price", 0)
            total_cost_cents = product.get("cost", 0)

            # Convert cents to USD
            unit_price_usd = unit_price_cents / 100
            total_cost_usd = total_cost_cents / 100

            # Compute per-minute rate in USD
            # (if duration > 0, distribute total cost over duration)
            per_minute_usd = (total_cost_usd / total_minutes) if total_minutes else 0

            converted_products.append({
                "product": product_name,
                # "unit_price_cents": round(unit_price_cents, 6),
                # "unit_price_usd": round(unit_price_usd, 6),
                # "cost_cents": round(total_cost_cents, 6),
                "cost_usd": round(total_cost_usd, 6),
                "per_minute_usd": round(per_minute_usd, 6),
            })

        return converted_products



    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p")
            if isinstance(v, datetime)
            else v,
        }




