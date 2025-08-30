from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    WS_SECRET: str = os.getenv("WS_SECRET", "secret")
    AGENT_TIMEOUT: int = int(os.getenv("AGENT_TIMEOUT", "20"))
    TOP_K: int = int(os.getenv("TOP_K", "5"))

settings = Settings()
