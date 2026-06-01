from typing import Optional
from pydantic import Field
from .base import BaseSchema


# ===== UNIVERSITIES =====

class UniversityItem(BaseSchema):
    id: int
    name_ru: str = Field(alias="nameRu")
    name_kz: str = Field(alias="nameKz")
    name_en: str = Field(alias="nameEn")
    protocol: Optional[str] = None
    url: str
    port: int
    context: Optional[str] = None
    expiry_date: Optional[str] = Field(None, alias="expiryDate")
    local_url: Optional[str] = Field(None, alias="localUrl")
    is_type: int
    has_access_to_mobile_platonus_student_app: bool = Field(alias="hasAccessToMobilePlatonusStudentApp")
    has_access_to_mobile_platonus_tutor_app: bool = Field(alias="hasAccessToMobilePlatonusTutorApp")
