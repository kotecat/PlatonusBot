from typing import Optional
from pydantic import BaseModel, Field
from .base import BaseSchema


# ===== REGIONS =====

class RegionItem(BaseSchema):
    id: int
    name_ru: str = Field(alias="nameRu")
    name_kz: str = Field(alias="nameKz")
    name_en: str = Field(alias="nameEn")
    code: Optional[str] = None
    information_system: Optional[str] = Field(None, alias="informationSystem")


# ===== COLLEGES =====

class NamedItem(BaseSchema):
    id: int
    name_ru: str = Field(alias="nameRu")
    name_kz: str = Field(alias="nameKz")
    name_en: str = Field(alias="nameEn")


class CatoRegion(BaseSchema):
    name_ru: str = Field(alias="nameRu")
    name_kz: str = Field(alias="nameKz")
    name_en: str = Field(alias="nameEn")
    code_prefix: int = Field(alias="codePrefix")
    priority: int


class Cato(BaseSchema):
    id: int
    code: str
    name_ru: str = Field(alias="nameRu")
    name_kz: str = Field(alias="nameKz")
    short_name_ru: str = Field(alias="shortNameRu")
    short_name_kz: str = Field(alias="shortNameKz")
    region: CatoRegion
    status: int


class CollegeItem(BaseSchema):
    id: int
    code: Optional[str] = None
    name_ru: str = Field(alias="nameRu")
    name_kz: str = Field(alias="nameKz")
    name_en: str = Field(alias="nameEn")
    type: Optional[NamedItem] = None
    state: Optional[NamedItem] = None
    creation_type: Optional[NamedItem] = Field(None, alias="creationType")
    cato: Optional[Cato] = None
    cato_region: Optional[CatoRegion] = Field(None, alias="catoRegion")
    open_year: Optional[int] = Field(None, alias="openYear")
    close_year: Optional[int] = Field(None, alias="closeYear")
    email: Optional[str] = None
    url: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    context: Optional[str] = None
    expiry_date: Optional[int] = Field(None, alias="expiryDate")
    local_url: Optional[str] = Field(None, alias="localUrl")
    is_type: Optional[int] = Field(None, alias="isType")
    table_type: Optional[int] = Field(None, alias="tableType")
    has_access_to_mobile_platonus_student_app: bool = Field(alias="hasAccessToMobilePlatonusStudentApp")
    has_access_to_mobile_platonus_tutor_app: bool = Field(alias="hasAccessToMobilePlatonusTutorApp")
