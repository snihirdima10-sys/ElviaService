from aiogram.fsm.state import StatesGroup, State


class CreateOrderState(StatesGroup):
    wait_for_choose_period = State()
    wait_for_terms_confirmation = State()
    wait_for_city = State()
    wait_for_delivery_method = State()
    wait_for_address = State()
    wait_for_delivery_data = State()
    wait_for_order_confirmation = State()
    wait_for_payment = State()