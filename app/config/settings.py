import uuid
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

__all__ = ["settings", "async_session_maker", "DATABASE_URL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)

    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    DEBUG: bool
    APP_PORT: int

    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr

    # JWT_ACCESS_SECRET_KEY: SecretStr
    # JWT_ACCESS_ALGORITHM: str
    # JWT_ACCESS_EXPIRE: str
    #
    # JWT_REFRESH_ALGORITHM: str
    # JWT_REFRESH_EXPIRE: str


settings = Settings()
DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    username=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD.get_secret_value(),
    database=settings.POSTGRES_DB,
)

async_db_engine = create_async_engine(
    url=DATABASE_URL,
    pool_use_lifo=True,
    max_overflow=5,
    pool_size=25,
    connect_args={
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)

async_session_maker = async_sessionmaker(
    bind=async_db_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
