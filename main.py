import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from handlers import plt_router
from config import app_config
from core import bot
from notify import safe_check_loop

j_storage = Path(app_config.JOURNAL_DIRECTORY)
j_storage.mkdir(parents=True, exist_ok=True)

s_storage = Path(app_config.SETTINGS_DIRECTORY)
s_storage.mkdir(parents=True, exist_ok=True)

a_storage = Path(app_config.AUTH_DIRECTORY)
a_storage.mkdir(parents=True, exist_ok=True)


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Приветствие и инструкция по использованию бота"),
            BotCommand(command="login", description="Сохранить логин и пароль для доступа к журналу"),
            BotCommand(command="journal", description="Получить информацию о своих оценках"),
        ]
    )
    

async def main() -> None:
    dp = Dispatcher()
    
    dp.include_router(plt_router)

    asyncio.create_task(safe_check_loop(bot))
    
    await set_default_commands(bot)    
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    asyncio.run(main())
