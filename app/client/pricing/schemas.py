from uuid import UUID
from datetime import datetime
from pydantic import (
    BaseModel,
    Field,
    computed_field,
)
from typing import (
    Optional, 
    Dict,
    Any
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


    @computed_field(return_type=str)
    def formatted_duration(self) -> Optional[str]:
        """Convert duration from milliseconds → HH:MM:SS"""
        if not self.duration_ms:
            return None
        total_seconds = int(self.duration_ms / 1000)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"


    @computed_field(return_type=str)
    def user_sentiment(self) -> Optional[str]:
        """Extract user sentiment from call_analysis"""
        return self.call_analysis.get("user_sentiment") if self.call_analysis else None


    @computed_field(return_type=str)
    def call_successful(self) -> Optional[str]:
        """Convert boolean → readable status"""
        if not self.call_analysis:
            return None
        status = self.call_analysis.get("call_successful")
        if status is True:
            return "Successful"
        elif status is False:
            return "Unsuccessful"
        return None


    @computed_field(return_type=float)
    def total_cost_usd(self) -> Optional[float]:
        """Convert combined_cost (in cents) → USD"""
        if self.call_cost and "combined_cost" in self.call_cost:
            return round(self.call_cost["combined_cost"] / 100, 3)
        return None


    # @computed_field(return_type=List[Dict[str, Any]])
    # def product_costs_usd(self) -> Optional[List[Dict[str, Any]]]:
    #     """
    #     Convert each product cost in cents → USD.
    #     Keeps structure, just replaces cost with USD value.
    #     """
    #     if not self.call_cost or "product_costs" not in self.call_cost:
    #         return None

    #     converted_products = []
    #     for product in self.call_cost["product_costs"]:
    #         converted_products.append({
    #             "product": product.get("product"),
    #             "unit_price": product.get("unit_price"),
    #             # ✅ Convert cents → USD safely
    #             "cost_usd": round(product.get("cost", 0) / 100, 3)
    #         })
    #     return converted_products


    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p")
            if isinstance(v, datetime)
            else v,
        }




