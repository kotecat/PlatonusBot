from pydantic import Field
from .base import BaseSchema


# ===== UNIVERSITY / TERM / YEAR =====

class CurrentTerm(BaseSchema):
    value: str
    key: str


class TermItem(BaseSchema):
    name: str
    id: int = Field(alias="ID")


class Terms(BaseSchema):
    terms: list[TermItem]


class Years(BaseSchema):
    years: list[int]


class StudyRoomYearItem(BaseSchema):
    name: str
    id: str = Field(alias="ID")


class StudyRoomsYears(BaseSchema):
    years: list[StudyRoomYearItem]


class CurrentYear(BaseSchema):
    current_year: int = Field(alias="currentYear")
