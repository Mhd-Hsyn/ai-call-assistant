from uuid import UUID
from datetime import datetime
from pydantic import (
    BaseModel,
    EmailStr,
    Field, 
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



#### Campaign ####

class CampaignCreatePayloadSchema(BaseModel):
    agent_uid : UUID = Field(..., description="Agent UUID")
    name : str


class CampaignFilterParams(BaseModel):
    id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    name: Optional[str] = None
    is_deleted: Optional[bool] = None


class AgentShortInfoSchema(BaseModel):
    id : UUID
    agent_id: str
    agent_name: str

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p")
            if isinstance(v, datetime)
            else v,
        }


class CampaignInfoSchema(BaseModel):
    id: UUID
    name: str
    created_at : datetime
    agent: AgentShortInfoSchema

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p")
            if isinstance(v, datetime)
            else v,
        }



class CampaignModifyPayloadSchema(BaseModel):
    campaign_uid : UUID = Field(..., description="Campaign UUID")
    agent_uid : Optional[UUID] = Field(default=None, description="Agent UUID")
    name : Optional[str] = None



#### Campaign Contact ####


class CampaignContactCreatePayloadSchema(BaseModel):
    campaign_uid : UUID = Field(..., description="Campaign UUID")
    phone_number: str = Field(..., description="Valid phone number")
    first_name: Optional[str] = None 
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    dynamic_variables: Optional[Dict[str, Any]]  = None


class CampaignContactResponseSchema(BaseModel):
    id : UUID
    phone_number: str = Field(..., description="Valid phone number")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    created_at : datetime
    dynamic_variables: Optional[Dict[str, Any]]  = None

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.strftime("%d %b %Y, %I:%M %p")
            if isinstance(v, datetime)
            else v,
        }



class CampaignContactFilterParams(BaseModel):
    id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

   

class CampaignContactModifyPayloadSchema(BaseModel):
    campaign_contact_uid : UUID = Field(..., description="Campaign Contact UUID")
    phone_number: str = Field(..., description="Valid phone number")
    first_name: Optional[str] = None 
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    dynamic_variables: Optional[Dict[str, Any]]  = None


