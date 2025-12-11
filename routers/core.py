from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from schemas.schemas import ExtensionSchema, ScanRequest, SearchRequest, SearchAllExtensionsInfo, SearchAllExtensionsAllInfo
from core.deps import get_db
from scanner import service

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

@router.get("/searchExtension", response_model=ExtensionSchema)
def search_extension(
    params: SearchRequest = Depends(),
    db: Session = Depends(get_db)
):
    try:
        result = service.search_extension_by_name(db=db, extension_name=params.name)
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in search_extension: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/getExtensionsBaseInfo", response_model=List[SearchAllExtensionsInfo])
def get_extensions_base_info(db: Session = Depends(get_db)):
    try:
        result = service.get_all_extensions_basic(db)
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in get_extensions_base_info: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/getExtensionsAllInfo", response_model=List[SearchAllExtensionsAllInfo])
def get_extensions_all_info(db: Session = Depends(get_db)):
    try:
        result = service.get_all_extensions_all(db)
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in get_extensions_all_info: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



@router.post("/createExtension", response_model=ExtensionSchema)
def create_extension(request: ScanRequest, db: Session = Depends(get_db)):
    try:
        result = service.create_extension_by_name(db, request.name)
        if result is None:
            raise HTTPException(status_code=404, detail="Extension not found")
        return result
    except ValueError as e:
        # Catch duplicate extension error from CRUD
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        print(f"Error in create_extension: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
        
