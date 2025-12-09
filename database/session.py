from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import Settings

settings = Settings()

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)