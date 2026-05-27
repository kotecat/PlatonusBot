from aiogram.fsm.state import State, StatesGroup


class LoginStates(StatesGroup):
    waiting_university = State()
    waiting_credentials = State()
