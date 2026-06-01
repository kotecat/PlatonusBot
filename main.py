# PlatonusBot — Telegram bot for tracking grade changes in Platonus LMS
# Copyright (C) 2026  kotecat <kotik@ikote.ru>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from handlers import router
from config import app_config
from core import bot
from bot_ui.notify import safe_check_loop


def setup_storage_directories():
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
            BotCommand(command="profile", description="Показать информацию о профиле"),
        ]
    )
    

async def main() -> None:
    setup_storage_directories()
    
    dp = Dispatcher()
    
    dp.include_router(router)

    # if app_config.AUTO_CHECK_ENABLED:
    #     asyncio.create_task(safe_check_loop(bot))

    await set_default_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    asyncio.run(main())
