from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

@asynccontextmanager
async def mongo_transaction():
    async with await client.start_session() as session:
        async with session.start_transaction():
            yield session
