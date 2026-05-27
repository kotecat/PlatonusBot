from os import path

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from api.p_api import PlatonusApi, get_universities
from utils import save_json
from config import app_config
from states import LoginStates
from keyboards.login import (
    UniversityCallback,
    build_university_keyboard
)


router = Router()

_universities_cache: list[dict] = []


async def _get_universities() -> list[dict]:
    global _universities_cache
    if not _universities_cache:
        _universities_cache = await get_universities()
    return _universities_cache


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        "<b>👋 Привет! Я бот для отслеживания изменений в журнале Платонус.</b>\n\n"
        "Для начала привяжи свой аккаунт:\n"
        "/login — выбрать университет и войти\n\n"
        "После этого:\n"
        "/journal — посмотреть текущие оценки\n"
        "Бот будет сам присылать уведомления при изменении оценок.",
        parse_mode=ParseMode.HTML
    )


# ---------- /login ----------

@router.message(Command(commands=["login", "l", "user", "u"]))
async def command_login_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(LoginStates.waiting_university)
    await message.answer(
        "🏫 <b>Введите название университета</b> для поиска:\n"
        "<i>Например: КЭУ, Карагандинский, Назарбаев...</i>",
        parse_mode=ParseMode.HTML
    )


# ---------- Поиск университета ----------

@router.message(LoginStates.waiting_university)
async def university_search_handler(message: Message, state: FSMContext) -> None:
    
    universities = await _get_universities()
    query = message.text.strip()
    keyboard = build_university_keyboard(universities, message.from_user.id, query)

    if not keyboard.inline_keyboard:
        await message.answer(f"❌ Ничего не найдено по запросу «{query}».\nПопробуйте другое название.")
        return

    await message.answer(
        f"🔍 Результаты по запросу «{query}»:",
        reply_markup=keyboard
    )


# ---------- Выбор университета ----------

@router.callback_query(UniversityCallback.filter())
async def university_select_handler(
    callback: CallbackQuery,
    callback_data: UniversityCallback,
    state: FSMContext
) -> None:
    if callback_data.user_id != callback.from_user.id:
        await callback.answer("Это не ваш запрос, игнорирую.", show_alert=True, cache_time=3)
        return
    
    universities = await _get_universities()

    uni = next((u for u in universities if u["id"] == callback_data.uni_id), None)
    if not uni:
        await callback.answer("Университет не найден, попробуйте снова.")
        return

    await state.update_data(uni_url=uni["url"])
    await state.set_state(LoginStates.waiting_credentials)

    await callback.message.edit_text(
        f"✅ <b>{uni['nameRu']}</b>\n\n"
        "Введите логин и пароль через пробел:\n"
        "<code>mylogin mypassword</code>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


# ---------- Ввод логина и пароля ----------

@router.message(LoginStates.waiting_credentials)
async def credentials_handler(message: Message, state: FSMContext) -> None:
    args = message.text.strip().split()

    if len(args) < 2:
        await message.answer(
            "Введите логин и пароль через пробел:\n"
            "<code>mylogin mypassword</code>",
            parse_mode=ParseMode.HTML
        )
        return

    login, password = args[0], args[1]
    data = await state.get_data()
    uni_url = data["uni_url"]

    try:
        async with PlatonusApi(host=uni_url, login=login, password=password) as api:
            await api.authenticate()
    except Exception as e:
        await message.answer(f"❌ Не удалось авторизоваться: {e}\n\nПроверьте логин и пароль.")
        return

    save_json(
        {"login": login, "password": password, "host": uni_url},
        path.join(app_config.AUTH_DIRECTORY, f"{message.from_user.id}.json")
    )

    await state.clear()
    await message.answer(
        "✅ Данные сохранены! Используйте /journal для просмотра оценок.",
        parse_mode=ParseMode.HTML
    )
