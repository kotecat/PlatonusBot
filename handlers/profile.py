from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode

from api.p_api import PlatonusApi
from keyboards.start import build_start_keyboard
from utils import save_json, get_auth
from config import app_config


router = Router()


@router.message(Command(commands=["profile", "p", "me", "my", "info", "account"]))
async def command_start_handler(message: Message) -> None:
    creds = get_auth(message.from_user.id)  # Just to check if auth exists
    
    if not creds:
        await message.answer("Сначала привяжи аккаунт через /login")
        return

    login, password, host = creds
    
    async with PlatonusApi(host=host, login=login, password=password) as api:
        user_info = await api.get_user_info()

    university = user_info.get("university", {})
    
    await message.answer(
        f"<b>👤 <u>Профиль пользователя</u></b>\n\n"
        
        f"<b>📛 Имя:</b> {user_info.get('fullName', 'Unknown')}\n"
        f"<b>🎂 Возраст:</b> {user_info.get('age', '0')}\n"
        f"<b>👥 Группа:</b> {user_info.get('groupName', 'Unknown')}\n"
        f"<b>📚 Курс:</b> {user_info.get('courseNumber', 'Unknown')}\n\n"

        f"<b>⭐ GPA:</b> {user_info.get('gpa', 'N/A')}\n\n"
        
        f"<b>🎓 Специальность:</b> {user_info.get('professionName', 'Unknown')}\n"
        f"<b>🏛️ УЗ:</b> {university.get('nameRu', 'Unknown')}\n",
        parse_mode=ParseMode.HTML,
    )


# ---------- /login ----------

# @router.callback_query(LoginCallback.filter())
# async def command_login_callback_handler(
#     callback_query: CallbackQuery,
#     callback_data: LoginCallback,
#     state: FSMContext
# ) -> None:
#     if callback_data.user_id != callback_query.from_user.id:
#         await callback_query.answer("Это не твой запрос!", show_alert=True, cache_time=10)
#         return
    
#     await state.set_state(LoginStates.waiting_university)
#     await callback_query.message.delete()
#     await callback_query.message.answer(
#         "🏫 <b>Введите название университета</b> для поиска:\n"
#         "<i>Например: КЭУ, Карагандинский, Назарбаев...</i>",
#         parse_mode=ParseMode.HTML
#     )
#     await callback_query.answer(cache_time=10)
