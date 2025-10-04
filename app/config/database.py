from beanie import init_beanie
import motor.motor_asyncio

# import all models
from app.auth.models import (
    UserModel,
    UserWhitelistTokenModel
)
from app.config.settings import settings


async def init_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_uri)
    database = client[settings.mongo_db]

    # IMPORTANT: list all models here
    await init_beanie(
        database,
        document_models=[
            UserModel,
            UserWhitelistTokenModel
        ]
    )
