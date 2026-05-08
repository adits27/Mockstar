from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    google_api_key: str
    database_url: str

    model_config = ConfigDict(env_file=".env")


settings = Settings()
