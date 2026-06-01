from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils import translit
from schemas.university import UniversityItem
from schemas.college import RegionItem, CollegeItem


COLLEGE_LOGIN_ENABLED = True


class LoginCallback(CallbackData, prefix="login"):
    user_id: int


class InstitutionTypeCallback(CallbackData, prefix="inst_type"):
    user_id: int
    type: str  # "university" | "college"


class UniversityCallback(CallbackData, prefix="uni"):
    user_id: int
    uni_id: int


class RegionCallback(CallbackData, prefix="region"):
    user_id: int
    region_id: int


class CollegeCallback(CallbackData, prefix="college"):
    user_id: int
    college_id: int


def build_institution_type_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🏛 Университет",
        callback_data=InstitutionTypeCallback(user_id=user_id, type="university").pack()
    ))
    if COLLEGE_LOGIN_ENABLED:
        builder.row(InlineKeyboardButton(
            text="🎓 Колледж",
            callback_data=InstitutionTypeCallback(user_id=user_id, type="college").pack()
        ))
    return builder.as_markup()


def build_university_keyboard(universities: list[UniversityItem], user_id: int, query: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    q = query.lower().strip()
    q_lat = translit(q)

    filtered = [
        u for u in universities
        if (s := f"{u.name_ru} {u.name_kz} {u.name_en} {u.url}".lower())
        and (q in s or q_lat in s)
    ][:10]

    for u in filtered:
        builder.row(InlineKeyboardButton(
            text=u.name_ru,
            callback_data=UniversityCallback(user_id=user_id, uni_id=u.id).pack()
        ))
    return builder.as_markup()


def build_region_keyboard(regions: list[RegionItem], user_id: int, query: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    q = query.lower().strip()

    filtered = [
        r for r in regions
        if not q or q in f"{r.name_ru} {r.name_kz} {r.name_en}".lower()
    ][:10]

    for r in filtered:
        builder.row(InlineKeyboardButton(
            text=r.name_ru,
            callback_data=RegionCallback(user_id=user_id, region_id=r.id).pack()
        ))
    return builder.as_markup()


def build_college_keyboard(colleges: list[CollegeItem], user_id: int, query: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    q = query.lower().strip()
    q_lat = translit(q)

    filtered = [
        c for c in colleges
        if (s := f"{c.name_ru} {c.name_kz} {c.name_en} {c.url or ''}".lower())
        and (not q or q in s or q_lat in s)
    ][:10]

    for c in filtered:
        builder.row(InlineKeyboardButton(
            text=c.name_ru,
            callback_data=CollegeCallback(user_id=user_id, college_id=c.id).pack()
        ))
    return builder.as_markup()
