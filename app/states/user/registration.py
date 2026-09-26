from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    wait_for_name = State()
    wait_for_height = State()
    wait_for_current_weight = State()
    wait_for_target_weight = State()
    wait_for_phone = State()
    confirm_registration = State()