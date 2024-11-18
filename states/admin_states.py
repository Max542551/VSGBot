from aiogram.dispatcher.filters.state import StatesGroup, State


class AdminState(StatesGroup):
    BROADCAST = State()
    LOCATION = State()


class AdminFindOrder(StatesGroup):
    waiting_for_order_number = State()


class TaxiDriverInfoState(StatesGroup):
    CHANGE_CAR = State()
    CHANGE_COLOR = State()
    CHANGE_NUMBER = State()
    CHANGE_BALANCE = State()
    CHANGE_NAME = State()
    REQUEST_PHONE = State()


class UserInfoState(StatesGroup):
    CHANGE_NAME = State()
    REQUEST_PHONE = State()
