import json
import uuid
from datetime import datetime
from beanie import Link
from fastapi import Form, File, UploadFile
from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import List, Optional, Any
from app.core.exceptions.handlers import (
    AppException
)
from app.core.constants.choices import (
    KnowledgeBaseStatusChoices,
    KnowledgeBaseSourceTypeChoices
)
from ..models import (
    KnowledgeBaseSourceModel
)



class SitemapRequest(BaseModel):
    website_url: HttpUrl



class KnowledgeBaseText(BaseModel):
    text: str = Field(..., description="Knowledge text content")
    title: str = Field(..., description="Knowledge text title")


class KnowledgeBaseBaseSchema(BaseModel):
    name: str = Field(..., min_length=1, description="Knowledge base name")
    knowledge_base_texts: Optional[List[KnowledgeBaseText]] = None
    knowledge_base_urls: Optional[List[str]] = None

    @field_validator("knowledge_base_urls")
    def validate_urls(cls, urls):
        if urls:
            for url in urls:
                if not isinstance(url, str) or not url.startswith("http"):
                    raise ValueError("Each URL must be a valid string starting with 'http'")
        return urls

    class Config:
        arbitrary_types_allowed = True  # Allow custom types like UploadFile
        extra = "allow"  # Allows dynamically adding attributes like `.files`


class KnowledgeBaseCreateForm(KnowledgeBaseBaseSchema):
    """Used to handle multipart/form-data inputs for knowledge base creation."""

    def __init__(
        self,
        name: str = Form(...),
        knowledge_base_texts: Optional[str] = Form(None),
        knowledge_base_urls: Optional[str] = Form(None),
        knowledge_base_files: Optional[List[UploadFile]] = File(None),
    ):
        # --- Parse and validate texts JSON ---
        parsed_texts = None
        if knowledge_base_texts:
            try:
                data = json.loads(knowledge_base_texts)
                if not isinstance(data, list):
                    raise ValueError
                parsed_texts = [KnowledgeBaseText(**item) for item in data]
            except Exception:
                raise AppException("Invalid 'knowledge_base_texts' JSON. Must be a list of {text, title}.")

        # --- Parse and validate URLs JSON ---
        parsed_urls = None
        if knowledge_base_urls:
            try:
                data = json.loads(knowledge_base_urls)
                if not isinstance(data, list):
                    raise ValueError
                parsed_urls = data
            except Exception:
                raise AppException("Invalid 'knowledge_base_urls' JSON. Must be a list of URLs.")

        # --- Ensure at least one source is provided ---
        if not any([parsed_texts, parsed_urls, knowledge_base_files]):
            raise AppException("At least one of texts, urls, or files is required.")

        # --- Initialize Pydantic base fields ---
        super().__init__(
            name=name,
            knowledge_base_texts=parsed_texts,
            knowledge_base_urls=parsed_urls,
        )

        # --- Attach files dynamically (allowed due to Config.extra="allow") ---
        self.files = knowledge_base_files
        self.texts = parsed_texts
        self.urls = parsed_urls




############  Response Scheema  ############

class APIBaseResponse(BaseModel):
    status: bool
    message: str
    data: Any | None = None



class KnowledgeBaseResponse(BaseModel):
    id: uuid.UUID
    knowledge_base_id: str
    name: str
    status: KnowledgeBaseStatusChoices
    user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v,
        }



class KnowledgeBaseSourceResponse(BaseModel):
    id: uuid.UUID
    source_id: str
    type: KnowledgeBaseSourceTypeChoices
    title: Optional[str] = None
    url: str
    created_at: datetime
    updated_at: datetime


    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v,
        }


class KnowledgeBaseDetailResponse(BaseModel):
    id: uuid.UUID
    knowledge_base_id: str
    name: str
    status: KnowledgeBaseStatusChoices
    created_at: datetime
    updated_at: datetime
    sources: List[KnowledgeBaseSourceResponse] = []
    # sources: Optional[List[Link[KnowledgeBaseSourceModel]]] = None  # 👈 reverse link

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v,
        }


class KnowledgeBaseInfoResponse(BaseModel):
    id: uuid.UUID
    knowledge_base_id: str
    name: str
    status: KnowledgeBaseStatusChoices
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v,
        }


