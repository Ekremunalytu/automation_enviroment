from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TESTZONE"
    ENV : str = "dev"
    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5433/postgres"

    class Config:
        env_file = ".env"
        extra = "ignore"


