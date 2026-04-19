from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)

    DATABASE_URL: str = "postgresql+asyncpg://recuser:recpass@postgres:5432/recengine"
    REDIS_URL: str = "redis://redis:6379/0"
    MODEL_VERSION: str = "v1"
    ARTIFACTS_DIR: str = "artifacts"

    ALS_FACTORS: int = 64
    ALS_ITERATIONS: int = 15
    ALS_REGULARIZATION: float = 0.01

    TWO_TOWER_DIM: int = 32
    TWO_TOWER_EPOCHS: int = 20
    TWO_TOWER_BATCH: int = 1024
    TWO_TOWER_LR: float = 1e-3

    EMBED_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_NLIST: int = 100
    FAISS_M: int = 8

    CANDIDATE_K: int = 500
    MMR_LAMBDA: float = 0.7


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
