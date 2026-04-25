from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    secret_key: str = "changeme"
    database_url: str = "postgresql+asyncpg://shipping:shipping@localhost:5432/shipping_manager"
    redis_url: str = "redis://localhost:6379/0"
    allowed_origins: str = "http://localhost:5173"
    default_page_size: int = 25
    max_page_size: int = 100


settings = Settings()
