from os import path

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from api.p_api import PlatonusApi, get_universities, get_regions_college, get_colleges_by_region
from utils import save_json, get_auth
from config import app_config
from states import LoginStates
from keyboards.login import (
    COLLEGE_LOGIN_ENABLED,
    LoginCallback, InstitutionTypeCallback,
    UniversityCallback, RegionCallback, CollegeCallback,
    build_institution_type_keyboard, build_university_keyboard,
    build_region_keyboard, build_college_keyboard,
)
from keyboards.start import build_start_keyboard
from schemas.university import UniversityItem
from schemas.college import RegionItem, CollegeItem


router = Router()

_universities_cache: list[UniversityItem] = []
_regions_cache: list[RegionItem] = []


async def _get_universities() -> list[UniversityItem]:
    global _universities_cache
    if not _universities_cache:
        _universities_cache = await get_universities()
    return _universities_cache


async def _get_regions() -> list[RegionItem]:
    global _regions_cache
    if not _regions_cache:
        _regions_cache = await get_regions_college()
    return _regions_cache


async def _ask_institution_type(target: Message, user_id: int, state: FSMContext):
    await state.set_state(LoginStates.waiting_institution_type)
    if COLLEGE_LOGIN_ENABLED:
        await target.answer(
            "Выберите тип учебного заведения:",
            reply_markup=build_institution_type_keyboard(user_id)
        )
    else:
        await state.set_state(LoginStates.waiting_university)
        await target.answer(
            "🏫 <b>Введите название университета</b> для поиска:\n"
            "<i>Например: КЭУ, Карагандинский, Назарбаев...</i>",
            parse_mode=ParseMode.HTML
        )


@router.message(CommandStart(deep_link=False))
async def command_start_handler(message: Message) -> None:
    creds = get_auth(message.from_user.id)  # Just to check if auth exists
    
    await message.answer(
        "<b>👋 Привет! Я бот для отслеживания изменений в журнале Платонус.</b>\n\n"
        "Для начала привяжи свой аккаунт:\n"
        "/login — выбрать университет и войти\n\n"
        "После этого:\n"
        "/journal — посмотреть текущие оценки\n"
        "Бот будет сам присылать уведомления при изменении оценок.",
        parse_mode=ParseMode.HTML,
        reply_markup=build_start_keyboard(message.from_user.id, is_login=(not bool(creds)))
    )


# ---------- /login ----------

@router.message(Command(commands=["login", "l", "user", "u"]))
async def command_login_handler(message: Message, state: FSMContext) -> None:
    await _ask_institution_type(message, message.from_user.id, state)


@router.callback_query(LoginCallback.filter())
async def login_callback_handler(
    callback: CallbackQuery,
    callback_data: LoginCallback,
    state: FSMContext
) -> None:
    if callback_data.user_id != callback.from_user.id:
        await callback.answer("Это не твой запрос!", show_alert=True, cache_time=10)
        return
    await callback.message.delete()
    await _ask_institution_type(callback.message, callback.from_user.id, state)
    await callback.answer(cache_time=10)


# ---------- Выбор типа ----------

@router.callback_query(InstitutionTypeCallback.filter())
async def institution_type_handler(
    callback: CallbackQuery,
    callback_data: InstitutionTypeCallback,
    state: FSMContext
) -> None:
    if callback_data.user_id != callback.from_user.id:
        await callback.answer("Это не твой запрос!", show_alert=True, cache_time=10)
        return

    if callback_data.type == "university":
        await state.set_state(LoginStates.waiting_university)
        await callback.message.answer(
            "🏫 <b>Введите название университета</b> для поиска:\n"
            "<i>Например: КЭУ, Карагандинский, Назарбаев...</i>",
            parse_mode=ParseMode.HTML
        )
    elif callback_data.type == "college" and COLLEGE_LOGIN_ENABLED:
        await state.set_state(LoginStates.waiting_region)
        regions = await _get_regions()
        await callback.message.answer(
            "🌍 <b>Введите название региона</b> для поиска или выберите из списка:",
            parse_mode=ParseMode.HTML,
            reply_markup=build_region_keyboard(regions, callback.from_user.id)
        )
    await callback.answer(cache_time=10)


# ---------- Университет ----------

@router.message(LoginStates.waiting_university)
async def university_search_handler(message: Message, state: FSMContext) -> None:
    universities = await _get_universities()
    keyboard = build_university_keyboard(universities, message.from_user.id, message.text.strip())

    if not keyboard.inline_keyboard:
        await message.answer(f"❌ Ничего не найдено по запросу «{message.text}».\nПопробуйте другое название.")
        return
    await message.answer(f"🔍 Результаты по запросу «{message.text}»:", reply_markup=keyboard)


@router.callback_query(UniversityCallback.filter())
async def university_select_handler(
    callback: CallbackQuery,
    callback_data: UniversityCallback,
    state: FSMContext
) -> None:
    if callback_data.user_id != callback.from_user.id:
        await callback.answer("Это не ваш запрос.", show_alert=True, cache_time=3)
        return

    universities = await _get_universities()
    uni = next((u for u in universities if u.id == callback_data.uni_id), None)
    if not uni:
        await callback.answer("Университет не найден, попробуйте снова.")
        return

    await state.update_data(host=uni.url)
    await state.set_state(LoginStates.waiting_credentials)
    await callback.message.answer(
        f"✅ <b>{uni.name_ru}</b>\n\n"
        "Введите логин и пароль через пробел:\n"
        "<code>mylogin mypassword</code>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer(cache_time=30)


# ---------- Регион ----------

@router.message(LoginStates.waiting_region)
async def region_search_handler(message: Message, state: FSMContext) -> None:
    regions = await _get_regions()
    keyboard = build_region_keyboard(regions, message.from_user.id, message.text.strip())

    if not keyboard.inline_keyboard:
        await message.answer(f"❌ Регион «{message.text}» не найден.\nПопробуйте другое название.")
        return
    await message.answer(f"🔍 Результаты по запросу «{message.text}»:", reply_markup=keyboard)


@router.callback_query(RegionCallback.filter())
async def region_select_handler(
    callback: CallbackQuery,
    callback_data: RegionCallback,
    state: FSMContext
) -> None:
    if callback_data.user_id != callback.from_user.id:
        await callback.answer("Это не ваш запрос.", show_alert=True, cache_time=3)
        return

    await state.update_data(region_id=callback_data.region_id)
    await state.set_state(LoginStates.waiting_college)
    await callback.message.answer(
        "🎓 <b>Введите название колледжа</b> для поиска:",
        parse_mode=ParseMode.HTML
    )
    await callback.answer(cache_time=10)


# ---------- Колледж ----------

@router.message(LoginStates.waiting_college)
async def college_search_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    colleges = await get_colleges_by_region(data["region_id"])
    keyboard = build_college_keyboard(colleges, message.from_user.id, message.text.strip())

    if not keyboard.inline_keyboard:
        await message.answer(f"❌ Колледж «{message.text}» не найден.\nПопробуйте другое название.")
        return

    await state.update_data(colleges=CollegeItem.dump_list(colleges))
    await message.answer(f"🔍 Результаты по запросу «{message.text}»:", reply_markup=keyboard)


@router.callback_query(CollegeCallback.filter())
async def college_select_handler(
    callback: CallbackQuery,
    callback_data: CollegeCallback,
    state: FSMContext
) -> None:
    if callback_data.user_id != callback.from_user.id:
        await callback.answer("Это не ваш запрос.", show_alert=True, cache_time=3)
        return

    data = await state.get_data()
    colleges = [CollegeItem.model_validate(c) for c in data["colleges"]]
    college = next((c for c in colleges if c.id == callback_data.college_id), None)

    if not college or not college.url:
        await callback.answer("Колледж не найден или не имеет URL.", show_alert=True)
        return

    await state.update_data(host=college.url)
    await state.set_state(LoginStates.waiting_credentials)
    await callback.message.answer(
        f"✅ <b>{college.name_ru}</b>\n\n"
        "Введите логин и пароль через пробел:\n"
        "<code>mylogin mypassword</code>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer(cache_time=30)


# ---------- Credentials ----------

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
    host = data["host"]

    try:
        async with PlatonusApi(host=host, login=login, password=password) as api:
            await api.authenticate()
    except Exception as e:
        await message.answer(f"❌ Не удалось авторизоваться: {e}\n\nПроверьте логин и пароль.")
        return

    save_json(
        {"login": login, "password": password, "host": host},
        path.join(app_config.AUTH_DIRECTORY, f"{message.from_user.id}.json")
    )
    await state.clear()
    await message.answer(
        "✅ Данные сохранены! Используйте /journal для просмотра оценок.",
        parse_mode=ParseMode.HTML,
        reply_markup=build_start_keyboard(message.from_user.id, is_login=False)
    )