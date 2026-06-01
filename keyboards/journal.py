from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from schemas.terms import (
    Terms,
    Years
)


class JournalCallback(CallbackData, prefix="jour"):
    user_id: int
    year: int
    semester: int
    is_back: bool = False
    has_period: bool = True


class JournalFinishCallback(CallbackData, prefix="jour_f"):
    user_id: int
    year: int
    semester: int
    is_open: bool = False
    has_period: bool = True

    
async def journal_semester_keyboard(
    user_id: int,
    current_year: int,
    current_semester: int,
    semesters: Terms
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for i, sem in enumerate(semesters.terms, start=1):
        name = sem.name
        id = sem.id
        
        builder.row(
            InlineKeyboardButton(
                text=('✅ ' if id == current_semester else '') + name,
                callback_data=JournalFinishCallback(
                    user_id=user_id,
                    year=current_year,
                    semester=id
                ).pack()
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=JournalCallback(
                user_id=user_id,
                year=current_year,
                semester=current_semester,
                is_back=True
            ).pack()
        )
    )
    
    return builder.as_markup()


async def journal_year_keyboard(
    user_id: int,
    current_year: int,
    current_semester: int,
    current_semester_name: str,
    years: Years,
    max_year: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    buttons_row = []
    
    for year in years.years:
        if year > max_year:
            continue
        buttons_row.append(
            InlineKeyboardButton(
                text=('✅ ' if year == current_year else '') + str(year),
                callback_data=JournalCallback(
                    user_id=user_id,
                    year=year,
                    semester=current_semester
                ).pack()
            )
        )
    
    builder.row(*buttons_row)
    builder.row(
        InlineKeyboardButton(
            text="Семестр: " + current_semester_name,
            callback_data=JournalFinishCallback(
                user_id=user_id,
                year=current_year,
                semester=current_semester,
                is_open=True
            ).pack()
        )
    )
    
    return builder.as_markup()
