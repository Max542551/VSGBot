from aiogram.dispatcher.filters.state import StatesGroup, State


class TaxiRegistrationState(StatesGroup):
    name = State()  # state 1
    phone = State()  # state 2
    car = State()  # state 3
    color_car = State()  # state 4
    registration_number = State()  # state 5
    child_seat = State()  # state 6
    waiting_for_payment_screenshot = State()  # state 7
    awaiting_admin_decision = State()


class TaxiLocationState(StatesGroup):
    SEND_LOCATION = State()


class TaxiState(StatesGroup):
    waiting_for_top_up_amount = State()
    waiting_for_payment_screenshot = State()


class Form(StatesGroup):
    amount = State()


class BanDriverStates(StatesGroup):
    waiting_for_reason = State()
