from aiogram import Router

from . import journal
from . import login


router = Router()

router.include_router(login.router)
router.include_router(journal.router)


__all__ = ["router"]
