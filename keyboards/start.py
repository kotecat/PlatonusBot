from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from .login import LoginCallback
from .journal import JournalCallback


def build_start_keyboard(
    user_id: int,
    is_login: bool = False
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_login:
        builder.row(
            InlineKeyboardButton(
                text="🔐 Войти в аккаунт",
                callback_data=LoginCallback(user_id=user_id).pack()
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="📓 Мой журнал",
                callback_data=JournalCallback(
                    user_id=user_id,
                    year=0,
                    semester=0,
                    is_back=False,
                    has_period=False
                ).pack()
            )
        )
    return builder.as_markup()
