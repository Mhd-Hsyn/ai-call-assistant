import uuid
from datetime import datetime
from beanie import Document
from pydantic import BaseModel, Field

class BaseDocument(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        use_state_management = True
        json_encoders = {uuid.UUID: str}

    class Config:
        json_encoders = {uuid.UUID: str}

    async def save(self, *args, **kwargs):
        self.__class__.model_validate(self.model_dump())

        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)
