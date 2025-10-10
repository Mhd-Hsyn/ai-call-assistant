from beanie import Link
from pydantic import Field
from app.core.models.base import BaseDocument
from app.auth.models import UserModel
from app.core.constants.choices import (
    KnowledgeBaseStatusChoices,
    KnowledgeBaseSourceTypeChoices,

)


class KnowledgeBaseModel(BaseDocument):
    user: Link[UserModel]
    knowledge_base_id: str = Field(..., index=True, unique=True)
    name: str
    status: KnowledgeBaseStatusChoices = KnowledgeBaseStatusChoices.IN_PROGRESS

    class Settings:
        name = "knowledge_bases"


class KnowledgeBaseSourceModel(BaseDocument):
    knowledge_base: Link[KnowledgeBaseModel]
    source_id: str = Field(..., index=True, unique=True)
    type : KnowledgeBaseSourceTypeChoices
    title : str | None = None
    url : str

    class Settings:
        name = "knowledge_base_sources"


