from aiogram.fsm.state import State, StatesGroup

class UpdateWeightState(StatesGroup):
    show_weight = State()
    wait_for_weight = State()
    confirm_weight = State()