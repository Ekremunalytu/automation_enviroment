from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Union, Dict, Any


class ExtensionSchema(BaseModel):
    """Extension bilgilerini temsil eden Pydantic modeli."""
    
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    
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


class ScanRequest(BaseModel):
    """Extension oluşturma isteği için şema."""
    name: str = Field(..., min_length=1, description="Extension name to create")


class SearchRequest(BaseModel):
    """Extension arama isteği için şema."""
    name: str = Field(..., min_length=1, description="Extension name to search")


class SearchAllExtensionsInfo(BaseModel):
    """Tüm extensionlar ile ilgili sınırlı bilgileri döndürür."""
    
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    
    id: int
    name: str
    publisher: str
    description: Optional[str] = None
    icon: Optional[str] = None


class SearchAllExtensionsAllInfo(ExtensionSchema):
    """Extension'ın tüm bilgilerini ID ile birlikte döndürür."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int



