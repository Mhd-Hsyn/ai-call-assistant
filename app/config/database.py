from beanie import init_beanie
from bson.codec_options import CodecOptions, UuidRepresentation
import motor.motor_asyncio
from app.auth.models import (
    UserModel,
    UserWhitelistTokenModel
)
from app.client.models import (
    KnowledgeBaseModel,
    KnowledgeBaseSourceModel,
    ResponseEngineModel,
    AgentModel,
    CallModel,
    CampaignModel,
    CampaignContactsModel
)
from app.config.settings import settings


async def init_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        settings.mongo_uri,
        uuidRepresentation="standard",
    )

    database = client.get_database(settings.mongo_db).with_options(
        codec_options=CodecOptions(uuid_representation=UuidRepresentation.STANDARD)
    )
    database = client[settings.mongo_db]

    # IMPORTANT: list all models here
    await init_beanie(
        database,
        document_models=[
            UserModel,
            UserWhitelistTokenModel,
            KnowledgeBaseModel,
            KnowledgeBaseSourceModel,
            ResponseEngineModel,
            AgentModel,
            CallModel,
            CampaignModel,
            CampaignContactsModel
        ]
    )
