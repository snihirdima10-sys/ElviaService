from aiogram.fsm.state import State, StatesGroup

class AdminState(StatesGroup):
    show_admin_panel = State()

    wait_patient_data = State()
    show_patient = State()

    change_dose = State()
    wait_confirm_dose_change = State()
    confirmed_dose = State()

    show_therapy_history = State()

    show_category_orders = State()
    show_orders = State()
    show_order = State()