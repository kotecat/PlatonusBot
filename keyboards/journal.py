from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


class JournalCallback(CallbackData, prefix="jour"):
    user_id: int
    year: int
    semester: int
    is_back: bool = False


class JournalFinishCallback(CallbackData, prefix="jour_f"):
    user_id: int
    year: int
    semester: int
    is_open: bool = False

    
async def journal_semester_keyboard(
    user_id: int,
    current_year: int,
    current_semester: int,
    semesters: list[dict[str, str]]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for i, sem in enumerate(semesters, start=1):
        name = sem.get("name", f"Unknown Semester {i}")
        id = sem.get("ID", i)
        
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
    years: list[int]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    buttons_row = []
    for year in years:
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
