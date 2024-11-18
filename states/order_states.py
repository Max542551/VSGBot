from aiogram.dispatcher.filters.state import StatesGroup, State


class OrderStatus(StatesGroup):
    GENERATED = 'GENERATED'
    ACCEPTED = 'ACCEPTED'
    EXPECTATION = 'EXPECTATION'
    TRIP = 'TRIP'
    COMPLETED = 'COMPLETED'
    CANCELED = 'CANCELED'
    DEFERRED = 'DEFERRED'


class TaxiOrderState(StatesGroup):
    FIRST_LOCATION = State()
    SECOND_LOCATION = State()
    BABY_SEAT = State()
    PAYMENT_METHOD = State()
    COMMENT = State()
    COST = State()
    PASSENGERS = State()
    SPECIFY_AMOUNT = State()


class ProposePriceState(StatesGroup):
    price = State()


class CancelOrderTaxi(StatesGroup):
    REASON = State()
