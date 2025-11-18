from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    ADMIN_LOGIN: str = "admin"
    ADMIN_PASSWORD: str
    ADMIN_SECRET_KEY: str
    BOT_TOKEN: str
    API_BASE: str = "http://localhost:8000/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

settings = Settings()