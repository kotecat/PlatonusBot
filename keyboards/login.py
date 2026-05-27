from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from utils import translit


class UniversityCallback(CallbackData, prefix="uni"):
    user_id: int
    uni_id: int


def build_university_keyboard(universities: list[dict], user_id: int, query: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    q = query.lower().strip()
    q_lat = translit(q)

    filtered = [
        u for u in universities
        if (
            s := f"{u.get('nameRu','')} {u.get('nameKz','')} {u.get('nameEn','')} {u.get('url','')}".lower()
        )
        and (q in s or q_lat in s)
    ][:10]

    for u in filtered:
        builder.row(
            InlineKeyboardButton(
                text=u["nameRu"],
                callback_data=UniversityCallback(user_id=user_id, uni_id=u["id"]).pack()
            )
        )

    return builder.as_markup()
