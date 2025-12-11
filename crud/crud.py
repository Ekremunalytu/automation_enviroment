from typing import Optional, List

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, load_only
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
# burada tüm extensionların tüm bilgileri getiriliyor
def get_extensions_all_info(db: Session) -> List[Extension]:
    return db.query(Extension).all()

def get_extensions_base_info(db: Session) -> List[Extension]:
    return db.query(Extension).options(load_only(Extension.id,Extension.name, Extension.publisher, Extension.description,Extension.icon)).all()

