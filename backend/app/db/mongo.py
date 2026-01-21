from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from app.core.config import settings
import certifi
from bson import ObjectId
from app.core.exceptions import DomainError

# --- Mongo Client (FIXED) ---
client = AsyncIOMotorClient(
    settings.MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=20000,
)

db = client[settings.MONGO_DB_NAME]


# --- Transactions ---
@asynccontextmanager
async def mongo_transaction():
    async with await client.start_session() as session:
        async with session.start_transaction():
            yield session


# --- ObjectId helper ---
def to_object_id(id_: str) -> ObjectId:
    try:
        return ObjectId(id_)
    except Exception:
        raise DomainError(f"Invalid ObjectId: {id_}")
