from aiogram.dispatcher.filters.state import State, StatesGroup


class UserRegistrationState(StatesGroup):
    name = State()  # state 1
    phone = State()  # state 2


class UserAddressChange(StatesGroup):
    waiting_for_home_address = State()  # Ожидание адреса дома
    waiting_for_work_address = State()  # Ожидание адреса работы


class StartState(StatesGroup):
    waiting_for_role = State()


class BanPassengerStates(StatesGroup):
    waiting_for_reason = State()
