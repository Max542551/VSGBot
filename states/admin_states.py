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

class ChangePhone(StatesGroup):
    GET_PHONE = State()
    CHANGE_TAXI_PHONE = State()
    CHANGE_USER_PHONE = State()

class ChangeRating(StatesGroup):
    GET_USER_ID = State()
    CHANGE_TAXI_RATING = State()
    CHANGE_USER_RATING = State()

class ChangeBusy(StatesGroup):
    GET_USER_ID = State()