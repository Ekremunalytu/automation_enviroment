from database.session import engine, SessionLocal
from models.models import Base, Extension
from crud.crud import get_extension_by_id
from routers.core import *
from fastapi import FastAPI




def main():
    app = FastAPI(
        title="ExTrace API",
        description="VS Code Extension Malware Scanner",
        version="1.0.0"
    )

    app.include_router(router)


if __name__ == "__main__":
    main()
