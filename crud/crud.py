from typing import Optional

from sqlalchemy.orm import Session
from models.models import Extension
from schemas.schemas import ExtensionSchema

def get_extension_by_id(db: Session, id: int) -> Optional[Extension]:
    return db.query(Extension).filter(Extension.id ==  id).first()

