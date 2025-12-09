from fastapi import APIRouter

router = APIRouter(
    tags=["core"]
)

@router.get("/")
def read_root():
    return {
        "Project": "Extrace",
        "Version": "0.1",
        "Status" : "Active",
        "Docs"   : "/docs"
    }

@router.get("/health")
def health_check():
    return {"status": "OK","service": "Extrace API"}