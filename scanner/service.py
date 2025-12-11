from fastapi import HTTPException
from sqlalchemy.orm import Session
from schemas.schemas import ExtensionSchema

# İsim karışıklığını önlemek için importu yeniden adlandırdım (alias)
from crud.crud import create_extension as create_db_extension
from crud.crud import search_extension_by_name as search_db_extension
from .json_parser import search_extension as find_json_in_dir
from crud.crud import get_extensions_all_info
from crud.crud import get_extensions_base_info


def get_all_extensions_basic(db: Session):
    all_extensions_basic_information = get_extensions_base_info(db)
    return all_extensions_basic_information

def get_all_extensions_all(db: Session):
    all_extensions_all_information = get_extensions_all_info(db)
    return all_extensions_all_information


def search_extension_by_name(db: Session, extension_name: str):
    # Veritabanında ara
    extension = search_db_extension(db, extension_name)
    # Eğer obje varsa Pydantic şemasına çevirmeye gerek yok,
    # FastAPI response_model bunu otomatik yapar ama manuel yapmak istersen:
    return extension


def create_extension_by_name(db: Session, extension_name: str):
    # 1. Klasörlerde JSON ara
    package_json = find_json_in_dir(extension_name)

    if package_json:
        # 2. JSON bulunduysa Şemaya çevir (Validasyon burada yapılır)
        package_schema = ExtensionSchema(**package_json)

        # 3. Veritabanına kaydet
        return create_db_extension(db, package_schema)

    return None

