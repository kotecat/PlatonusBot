import asyncio
import json
import logging
from pathlib import Path

from aiogram import Bot

from p_api import PlatonusApi
from utils import diff_journal, make_changes_string, save_json, load_json
from config import app_config
from core import bot

log = logging.getLogger(__name__)


AUTHS_DIR = Path("auths")
JOURNALS_DIR = Path("journals")

# --------------------- core ---------------------

async def check_user(bot: Bot, user_id: str, login: str, password: str):
    journal_path = JOURNALS_DIR / f"{user_id}__{login}.json"

    try:
        async with PlatonusApi(login=login, password=password) as api:
            new_journal = await api.get_journal(year=app_config.YEAR, semester=app_config.SEMESTER)
    except Exception as e:
        log.warning(f"[{user_id}] Ошибка при получении журнала: {e}")
        return

    old_journal = load_json(str(journal_path), default=[])

    save_json(new_journal, str(journal_path))

    if not old_journal:
        log.info(f"[{user_id}] Первый снимок сохранён.")
        return

    changes = diff_journal(old_journal, new_journal)

    if not changes:
        log.info(f"[{user_id}] Изменений нет.")
        return

    text = make_changes_string(changes)
    try:
        await bot.send_message(chat_id=int(user_id), text=text, parse_mode="HTML")
        log.info(f"[{user_id}] Отправлено {len(changes)} изменений.")
    except Exception as e:
        log.warning(f"[{user_id}] Не удалось отправить сообщение: {e}")


async def check_all(bot: Bot):
    if not AUTHS_DIR.exists():
        log.warning(f"Папка {AUTHS_DIR} не найдена.")
        return

    semaphore = asyncio.Semaphore(app_config.CONCURRENCY)

    async def check_with_limit(user_id: str, login: str, password: str):
        async with semaphore:
            await check_user(bot, user_id, login, password)

    tasks = []

    for auth_file in AUTHS_DIR.glob("*.json"):
        user_id = auth_file.stem

        try:
            with open(auth_file, "r", encoding="utf-8") as f:
                creds = json.load(f)
        except Exception as e:
            log.warning(f"Не удалось прочитать {auth_file.name}: {e}")
            continue

        login = creds.get("login")
        password = creds.get("password")

        if not login or not password:
            log.warning(f"[{user_id}] Нет login/password в файле.")
            continue

        tasks.append(check_with_limit(user_id, login, password))

    if not tasks:
        log.info("Нет аккаунтов для проверки.")
        return

    log.info(f"Запускаем проверку {len(tasks)} аккаунтов (concurrency={app_config.CONCURRENCY}).")
    await asyncio.gather(*tasks)


# checker.py

async def safe_check_loop(bot: Bot):
    """Фоновый цикл — запускается из main.py через create_task."""
    JOURNALS_DIR.mkdir(exist_ok=True)
    log.info("Чекер запущен.")

    running = asyncio.Lock()

    async def safe_check():
        if running.locked():
            log.warning("Предыдущий обход ещё не завершён — пропускаем тик.")
            return
        async with running:
            start = asyncio.get_event_loop().time()
            log.info("--- Начало обхода ---")
            await check_all(bot)
            elapsed = asyncio.get_event_loop().time() - start
            log.info(f"Обход завершён за {elapsed:.1f}с.")

    while True:
        asyncio.create_task(safe_check())
        await asyncio.sleep(app_config.CHECK_INTERVAL)


# if __name__ == "__main__" блок больше не нужен в checker.py

# --------------------- main ---------------------

async def main():
    JOURNALS_DIR.mkdir(exist_ok=True)
    log.info("Чекер запущен.")

    running = asyncio.Lock()

    async def safe_check():
        if running.locked():
            log.warning("Предыдущий обход ещё не завершён — пропускаем тик.")
            return
        async with running:
            start = asyncio.get_event_loop().time()
            log.info("--- Начало обхода ---")
            await check_all(bot)
            elapsed = asyncio.get_event_loop().time() - start
            log.info(f"Обход завершён за {elapsed:.1f}с.")

    try:
        while True:
            asyncio.create_task(safe_check())
            await asyncio.sleep(app_config.CHECK_INTERVAL)
    except (KeyboardInterrupt, asyncio.CancelledError):
        log.info("Чекер остановлен.")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())