from fastapi import FastAPI
from routers.core import router as core_router
from core.config import settings

def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="VS Code Extension Malware Scanner",
        version="1.0.0"
    )

    application.include_router(core_router)
    
    return application

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
