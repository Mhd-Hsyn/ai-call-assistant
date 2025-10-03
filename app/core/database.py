from beanie import init_beanie
import motor.motor_asyncio

# import all models
# from app.models.user import User
# from app.models.order import Order
# from app.models.product import Product
# from app.models.invoice import Invoice
# from app.models.chat import ChatMessage
from app.core.config import settings


async def init_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_uri)
    database = client[settings.mongo_db]

    # IMPORTANT: list all models here
    await init_beanie(
        database,
        document_models=[
            # User,
            # Order,
            # Product,
            # Invoice,
            # ChatMessage
        ]
    )
