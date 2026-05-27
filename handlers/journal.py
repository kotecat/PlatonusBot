import math
import logging
from os import path

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

from api.p_api import PlatonusApi
from utils import (
    save_json, load_json, diff_journal, 
    make_journal_string, make_changes_string, get_journal_path
)
from config import app_config
from keyboards.journal import (
    JournalCallback, JournalFinishCallback,
    journal_semester_keyboard, journal_year_keyboard
)


log = logging.getLogger(__name__)
router = Router()


async def get_semester_name(semester_id: int, terms: list[dict]) -> str:
    for term in terms:
        if int(term.get("ID", 0)) == semester_id:
            return term.get("name", f"Unknown Semester {semester_id}")
    return f"Unknown Semester {semester_id}"


def get_auth(user_id: int) -> tuple[str, str, str] | None:
    """Возвращает (login, password, host) или None если не авторизован."""
    auth_data = load_json(path.join(app_config.AUTH_DIRECTORY, f"{user_id}.json"), default={})
    login = auth_data.get("login")
    password = auth_data.get("password")
    host = auth_data.get("host")
    if not login or not password or not host:
        return None
    return login, password, host

# ---------- /journal ----------

@router.message(Command(commands=["journal", "j"]))
async def command_journal_handler(message: Message) -> None:
    creds = get_auth(message.from_user.id)
    if not creds:
        await message.answer("Сначала привяжи аккаунт через /login")
        return

    login, password, host = creds

    async with PlatonusApi(host=host, login=login, password=password) as api:
        current_year = (await api.get_current_year()).get("currentYear", app_config.YEAR)
        current_semester = int((await api.get_current_semester()).get("value", app_config.SEMESTER))
        journal = await api.get_journal(year=current_year, semester=current_semester)
        years = await api.get_journal_years()
        terms = await api.get_journal_semesters()

    journal_path = get_journal_path(message.from_user.id, login, current_year, current_semester)
    
    old_journal = load_json(journal_path, default=[])
    save_json(journal,journal_path)

    changes = diff_journal(old_journal, journal)
    
    journal_text = make_journal_string(journal)
    current_semester_name = await get_semester_name(current_semester, terms.get("terms", []))

    ikb = await journal_year_keyboard(
        user_id=message.from_user.id,
        current_year=current_year,
        current_semester=current_semester,
        current_semester_name=current_semester_name,
        years=years.get("years", [])
    )

    await message.answer(journal_text, parse_mode=ParseMode.HTML, reply_markup=ikb)

    if changes:
        await message.answer(make_changes_string(changes), parse_mode=ParseMode.HTML)


# ---------- Выбор года ----------

@router.callback_query(JournalCallback.filter())
async def journal_callback_handler(callback_query: CallbackQuery, callback_data: JournalCallback):
    user_id = callback_data.user_id
    year = callback_data.year
    semester = callback_data.semester
    is_back = callback_data.is_back

    creds = get_auth(user_id)
    if not creds:
        await callback_query.answer("Сначала привяжи аккаунт через /login", show_alert=True)
        return

    login, password, host = creds

    async with PlatonusApi(host=host, login=login, password=password) as api:
        years = await api.get_journal_years()
        terms = await api.get_journal_semesters()
        if not is_back:
            journal = await api.get_journal(year=year, semester=semester)
            journal_path = get_journal_path(callback_query.from_user.id, login, year, semester)

            old_journal = load_json(journal_path, default=[])
            save_json(journal,journal_path)

            changes = diff_journal(old_journal, journal)

    current_semester_name = await get_semester_name(semester, terms.get("terms", []))
    ikb = await journal_year_keyboard(
        user_id=user_id,
        current_year=year,
        current_semester=semester,
        current_semester_name=current_semester_name,
        years=years.get("years", [])
    )

    if is_back:
        await callback_query.message.edit_reply_markup(reply_markup=ikb)
    else:
        try:
            await callback_query.message.edit_text(
                make_journal_string(journal),
                parse_mode=ParseMode.HTML,
                reply_markup=ikb
            )
        except TelegramBadRequest as e:
            log.warning(f"[{user_id}] Не удалось отредактировать сообщение: {e}")

        if changes:
            await callback_query.message.answer(
                make_changes_string(changes, year=year, semester=current_semester_name),
                parse_mode=ParseMode.HTML
            )

    await callback_query.answer(cache_time=3)


# ---------- Выбор семестра ----------

@router.callback_query(JournalFinishCallback.filter())
async def journal_finish_callback_handler(callback_query: CallbackQuery, callback_data: JournalFinishCallback):
    user_id = callback_data.user_id
    year = callback_data.year
    semester = callback_data.semester
    is_open = callback_data.is_open

    creds = get_auth(user_id)
    if not creds:
        await callback_query.answer("Сначала привяжи аккаунт через /login", show_alert=True)
        return

    login, password, host = creds

    async with PlatonusApi(host=host, login=login, password=password) as api:
        terms = await api.get_journal_semesters()
        if not is_open:
            journal = await api.get_journal(year=year, semester=semester)
            
            journal_path = get_journal_path(callback_query.from_user.id, login, year, semester)

            old_journal = load_json(journal_path, default=[])
            save_json(journal,journal_path)

            changes = diff_journal(old_journal, journal)

    current_semester_name = await get_semester_name(semester, terms.get("terms", []))
    
    ikb = await journal_semester_keyboard(
        user_id=user_id,
        current_year=year,
        current_semester=semester,
        semesters=terms.get("terms", [])
    )

    if is_open:
        await callback_query.message.edit_reply_markup(reply_markup=ikb)
    else:
        try:
            await callback_query.message.edit_text(
                make_journal_string(journal),
                parse_mode=ParseMode.HTML,
                reply_markup=ikb
            )
        except TelegramBadRequest as e:
            log.warning(f"[{user_id}] Не удалось отредактировать сообщение: {e}")
            
        if changes:
            await callback_query.message.answer(
                make_changes_string(changes, year=year, semester=current_semester_name),
                parse_mode=ParseMode.HTML
            )
            
    await callback_query.answer(cache_time=3)
