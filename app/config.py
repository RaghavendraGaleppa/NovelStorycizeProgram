from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    MONGO_HOST: str = "mongodb"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "novel_reader_db"
    MONGO_ADMIN_DB: str = "admin"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # Server
    SERVER_PORT: int = 8000

    # Celery
    CELERY_CONCURRENCY: int = 4
    CELERY_WORKER_REPLICAS: int = 1
    CELERY_LOG_LEVEL: str = "info"

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb://{self.MONGO_INITDB_ROOT_USERNAME}:{self.MONGO_INITDB_ROOT_PASSWORD}"
            f"@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB}"
            f"?authSource={self.MONGO_ADMIN_DB}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
