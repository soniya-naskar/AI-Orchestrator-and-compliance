from motor.motor_asyncio import AsyncIOMotorClient
import aioredis
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from .config import settings

mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
db = mongo_client['orchestrator_db']

redis = None
async def init_redis():
    global redis
    redis = await aioredis.from_url(settings.REDIS_URL, encoding='utf-8', decode_responses=True)

def get_qdrant_client():
    # Assumes Qdrant running locally or accessible via QDRANT_URL
    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)
    return client
