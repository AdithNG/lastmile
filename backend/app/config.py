from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    secret_key: str = "dev_secret_key"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/lastmile"
    redis_url: str = "redis://localhost:6379"
    ors_api_key: str = ""
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"


settings = Settings()
