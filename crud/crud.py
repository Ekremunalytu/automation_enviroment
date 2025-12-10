from typing import Optional

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from models.models import Extension
from schemas.schemas import ExtensionSchema

def get_extension_by_id(db: Session, id: int) -> Optional[Extension]:
    return db.query(Extension).filter(Extension.id ==  id).first()

def search_extension_by_name(db: Session, name: str) -> Optional[Extension]:
    return db.query(Extension).filter(Extension.name == name).first()

def create_extension(db: Session, extension: ExtensionSchema) -> Extension:
    db_extension = Extension(**extension.model_dump())
    try:
        db.add(db_extension)
        db.commit()
        db.refresh(db_extension)
        return db_extension
    except IntegrityError:
        db.rollback()
        # Raised to be caught by the router for 409 Conflict
        raise ValueError("Extension already exists")
    except SQLAlchemyError as e:
        db.rollback()
        print("database commit error: ", e)
        raise e