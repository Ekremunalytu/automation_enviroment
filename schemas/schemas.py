from pydantic import BaseModel
from typing import Optional, List, Union, Dict, Any


class ExtensionSchema(BaseModel):
    # Zorunlu alanlar
    name: str
    publisher: str
    engines: Dict[str, Any]

    # Opsiyonel alanlar (Varsayılan None)
    license: Optional[str] = None
    displayName: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    galleryBanner: Optional[Dict[str, Any]] = None
    preview: Optional[bool] = None
    badges: Optional[List[Dict[str, Any]]] = None  # Liste içinde obje
    markdown: Optional[str] = None

    # QnA Union type örneği (String veya Boolean veya Dict olabilir)
    qna: Optional[Union[str, bool, Dict[str, Any]]] = None

    sponsor: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    pricing: Optional[str] = None
    main: Optional[str] = None
    web: Optional[str] = None

    # Bu ayar sayesinde package.json'daki fazlalık alanları görmezden gelir
    class Config:
        extra = "ignore"
        from_attributes = True # fastapi verisini otomatik bir şekilde jsona dönüştürmek için eklendi. 

class scanRequest(BaseModel):
    name: str

class searchRequest(BaseModel):
    name: str

