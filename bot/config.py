from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    API_BASE: str

    class Config:
        env_file = ".env"

settings = Settings()