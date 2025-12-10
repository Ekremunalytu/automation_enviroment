from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "ExTrace API"
    ENV: str = "dev"
    DATABASE_URL: PostgresDsn

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()



