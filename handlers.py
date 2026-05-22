import math
from os import path

from aiogram import Router
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from aiogram.enums import ParseMode

from p_api import PlatonusApi
from utils import save_json, load_json, diff_journal, make_journal_string, make_changes_string
from config import app_config


plt_router = Router()


@plt_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(
        "<b>👋 Привет! Я бот для отслеживания изменений в твоём электронном журнале Платонус.\n\n</b>"
        "Используй команду /login, чтобы сохранить свои данные для доступа к журналу.\n"
        "<i>Например: <code>/login mylogin mypassword</code>\n\n</i>"
        "После этого ты сможешь использовать команду /journal для получения информации о своих оценках.\n"
        "<i>Например: <code>/journal</code> или <code>/journal mylogin mypassword</code> (без сохранения данных авторизации)\n\n</i>",
        parse_mode=ParseMode.HTML
    )
    

@plt_router.message(Command(commands=["user", "u", "login", "l"]))
async def command_user_handler(message: Message, command: CommandObject) -> None:
    """
    This handler receives messages with `/user`, `/u`, `/login` or `/l` command
    """
    if not command.args:
        await message.answer("Пожалуйста, предоставьте логин и пароль в виде аргументов.\nНапример: `/login mylogin mypassword`")
        return
    
    args = command.args.split()
    
    if len(args) < 2:
        await message.answer("Пожалуйста, предоставьте логин и пароль в виде аргументов.\nНапример: `/login mylogin mypassword`")
        return
    
    login = command.args.split()[0]  # Assuming the first argument is the login
    password = command.args.split()[1]  # Assuming the second argument is the password
    
    try:
        async with PlatonusApi(login=login, password=password) as api:
            await api.authenticate()
    except Exception as e:
        await message.answer(f"Не удалось авторизоваться: {e}")
        return
    
    save_json(
        {"login": login, "password": password},
        path.join(app_config.AUTH_DIRECTORY, f"{message.from_user.id}.json")
    )
    
    await message.answer("Данные успешно сохранены! Теперь вы можете использовать команду /journal для получения информации о своих оценках.")


@plt_router.message(Command(commands=["journal", "j"]))
async def command_journal_handler(message: Message, command: CommandObject) -> None:
    """
    This handler receives messages with `/journal` or `/j` command
    """
    
    if command.args:
        args = command.args.split()
    else:
        args = []
    
    if len(args) < 2:
        auth_data = load_json(path.join(app_config.AUTH_DIRECTORY, f"{message.from_user.id}.json"), default={})
        login = auth_data.get("login")
        password = auth_data.get("password")
        if not login or not password:
            await message.answer("Пожалуйста, предоставьте логин и пароль в виде аргументов.\nНапример: `/login mylogin mypassword`")
            return
    else:
        login = command.args.split()[0]
        password = command.args.split()[1]
    
    async with PlatonusApi(login=login, password=password) as api:
        journal = await api.get_journal(year=2025, semester=2)
    
    old_journal = load_json(path.join(app_config.JOURNAL_DIRECTORY, f"{message.from_user.id}__{login}.json"), default=[])
    
    save_json(
        journal,
        path.join(app_config.JOURNAL_DIRECTORY, f"{message.from_user.id}__{login}.json")
    )
    
    changes = []
    if old_journal:
        changes = diff_journal(old_journal, journal)
    
    journal_text = make_journal_string(journal)
    changes_text = make_changes_string(changes)
    
    await message.answer(journal_text, parse_mode=ParseMode.HTML)
    await message.answer(changes_text, parse_mode=ParseMode.HTML)
