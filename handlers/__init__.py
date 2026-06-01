from aiogram import Router

from . import journal
from . import login
from . import profile


router = Router()

router.include_router(login.router)
router.include_router(journal.router)
router.include_router(profile.router)


__all__ = ["router"]
