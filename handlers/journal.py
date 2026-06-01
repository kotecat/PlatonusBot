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
    save_json, load_json, diff_journal, get_auth,
    make_journal_string, make_changes_string, get_journal_path
)
from config import app_config
from keyboards.journal import (
    JournalCallback, JournalFinishCallback,
    journal_semester_keyboard, journal_year_keyboard
)
from schemas.journal import Journal
from schemas.terms import (
    Terms, CurrentTerm,
    CurrentYear, Years, StudyRoomsYears
)


log = logging.getLogger(__name__)
router = Router()


async def get_semester_name(semester_id: int | str, terms: Terms) -> str:
    semester_id = int(semester_id)
    
    for term in terms.terms:
        if term.id == semester_id:
            return term.name
    return f"Unknown Semester {semester_id}"


def is_semester_exists(semester_id: int | str, terms: Terms) -> bool:
    semester_id = int(semester_id)
    
    for term in terms.terms:
        if term.id == semester_id:
            return True
    return False


async def get_journal_data(
    api: PlatonusApi,
    user_id: int,
    login: str,
    year: int,
    semester: int,
    semester_name: str = "1"
) -> tuple[list[Journal], str, list[dict], str]:
    journal = await api.get_journal(year=year, semester=semester)
    
    journal_path = get_journal_path(user_id, login, year, semester)
    old_journal = [Journal.model_validate(item) for item in load_json(journal_path, default=[])]
    
    save_json(Journal.dump_list(journal), journal_path)
    
    changes = diff_journal(old_journal, journal)
    changes_text = make_changes_string(changes, year=year, semester=semester_name) if changes else ""

    journal_text = make_journal_string(journal)

    return journal, journal_text, changes, changes_text


# ---------- /journal ----------

@router.message(Command(commands=["journal", "j"]))
async def command_journal_handler(message: Message) -> None:
    creds = get_auth(message.from_user.id)
    if not creds:
        await message.answer("Сначала привяжи аккаунт через /login")
        return

    login, password, host = creds
    m_user_id = message.from_user.id

    async with PlatonusApi(host=host, login=login, password=password) as api:
        current_year = (await api.get_current_year()).current_year
        current_semester = (await api.get_current_semester()).value
        
        years = await api.get_journal_years()
        terms = await api.get_journal_semesters()
        
        if not is_semester_exists(current_semester, terms) and terms.terms:
            current_semester = terms.terms[0].id
        
        current_semester_name = await get_semester_name(current_semester, terms)
        
        journal, journal_text, changes, changes_text = await get_journal_data(
            api=api,
            user_id=m_user_id,
            login=login,
            year=current_year,
            semester=current_semester,
            semester_name=current_semester_name
        )
    
    ikb = await journal_year_keyboard(
        user_id=m_user_id,
        current_year=current_year,
        current_semester=current_semester,
        current_semester_name=current_semester_name,
        years=years,
        max_year=current_year
    )

    await message.answer(journal_text, parse_mode=ParseMode.HTML, reply_markup=ikb)

    if changes:
        await message.answer(changes_text, parse_mode=ParseMode.HTML)


# ---------- Выбор года ----------

@router.callback_query(JournalCallback.filter())
async def journal_callback_handler(callback_query: CallbackQuery, callback_data: JournalCallback):
    user_id = callback_data.user_id
    year = callback_data.year
    semester = callback_data.semester
    is_back = callback_data.is_back
    has_period = callback_data.has_period

    if user_id != callback_query.from_user.id:
        await callback_query.answer("Это не твой журнал!", show_alert=True, cache_time=10)
        return

    creds = get_auth(user_id)
    if not creds:
        await callback_query.answer("Сначала привяжи аккаунт через /login", show_alert=True)
        return

    login, password, host = creds
    m_user_id = callback_query.from_user.id

    async with PlatonusApi(host=host, login=login, password=password) as api:
        current_year = (await api.get_current_year()).current_year
        current_semester = (await api.get_current_semester()).value
        
        years = await api.get_journal_years()
        terms = await api.get_journal_semesters()
        
        if not has_period:
            year = current_year
            semester = current_semester
        
        if not is_semester_exists(semester, terms) and terms.terms:
            semester = terms.terms[0].id
        
        current_semester_name = await get_semester_name(semester, terms)
        
        if not is_back:
            journal, journal_text, changes, changes_text = await get_journal_data(
                api=api,
                user_id=m_user_id,
                login=login,
                year=year,
                semester=semester,
                semester_name=current_semester_name
            )

    ikb = await journal_year_keyboard(
        user_id=m_user_id,
        current_year=year,
        current_semester=semester,
        current_semester_name=current_semester_name,
        years=years,
        max_year=current_year
    )

    if is_back:
        await callback_query.message.edit_reply_markup(reply_markup=ikb)
    else:
        try:
            await callback_query.message.edit_text(
                journal_text,
                parse_mode=ParseMode.HTML,
                reply_markup=ikb
            )
        except TelegramBadRequest as e:
            log.warning(f"[{m_user_id}] Не удалось отредактировать сообщение: {e}")

        if changes:
            await callback_query.message.answer(
                changes_text,
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
    
    m_user_id = callback_query.from_user.id
    
    if user_id != m_user_id:
        await callback_query.answer("Это не твой журнал!", show_alert=True, cache_time=10)
        return

    creds = get_auth(user_id)
    if not creds:
        await callback_query.answer("Сначала привяжи аккаунт через /login", show_alert=True)
        return

    login, password, host = creds

    async with PlatonusApi(host=host, login=login, password=password) as api:
        terms = await api.get_journal_semesters()
        current_semester_name = await get_semester_name(semester, terms)
        
        if not is_open:
            journal, journal_text, changes, changes_text = await get_journal_data(
                api=api,
                user_id=m_user_id,
                login=login,
                year=year,
                semester=semester,
                semester_name=current_semester_name
            )

    ikb = await journal_semester_keyboard(
        user_id=m_user_id,
        current_year=year,
        current_semester=semester,
        semesters=terms
    )

    if is_open:
        await callback_query.message.edit_reply_markup(reply_markup=ikb)
    else:
        try:
            await callback_query.message.edit_text(
                journal_text,
                parse_mode=ParseMode.HTML,
                reply_markup=ikb
            )
        except TelegramBadRequest as e:
            log.warning(f"[{m_user_id}] Не удалось отредактировать сообщение: {e}")
            
        if changes:
            await callback_query.message.answer(
                changes_text,
                parse_mode=ParseMode.HTML
            )
            
    await callback_query.answer(cache_time=3)
