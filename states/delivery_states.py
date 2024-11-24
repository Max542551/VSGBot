from aiogram.dispatcher.filters.state import StatesGroup, State

class DeliveryStatus(StatesGroup):
    GENERATED = 'GENERATED'
    ACCEPTED = 'ACCEPTED'
    GET_PACKAGE = 'GET_PACKAGE'
    LEAVING = 'LEAVING'
    IN_PLACE = 'IN_PLACE'
    COMPLETED = 'COMPLETED'
    CANCELED = 'CANCELED'

class DeliveryState(StatesGroup):
    FIRST_LOCATION = State()
    SECOND_LOCATION = State()
    DELIVERY_DATE = State()
    PACKAGE_CONTENT = State()
    HOW_MUCH_PAY = State()
    PAYMENT_METHOD = State()
    COMMENT = State()
    COST = State()
    SPECIFY_AMOUNT = State()

class DeliveryProposePriceState(StatesGroup):
    price = State()

class BanDeliveryStates(StatesGroup):
    waiting_for_reason = State()

class BanCustomerStates(StatesGroup):
    waiting_for_reason = State()