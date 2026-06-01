from aiogram.fsm.state import State, StatesGroup


class LoginStates(StatesGroup):
    waiting_institution_type = State()
    waiting_university = State()
    waiting_region = State()
    waiting_college = State()
    waiting_credentials = State()
