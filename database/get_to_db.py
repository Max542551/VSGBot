from ast import Del
import json

from aiogram.types import InlineKeyboardButton
from geopy.distance import geodesic
from peewee import DoesNotExist

from config_data.config import geolocator, database
from database.database import Delivery, SentDeliveryItem, User, Order, Taxi, SentItem
from states.delivery_states import DeliveryStatus
from states.order_states import OrderStatus


async def get_user(user_id):
    user = User.get_or_none(User.user_id == user_id)
    return user


async def get_taxi(user_id):
    user = Taxi.get_or_none(Taxi.user_id == user_id)
    return user


def get_order_by_taxi_id(taxi_id):
    # Получаем заказ для такси, где статус заказа либо GENERATED, ACCEPTED, либо EXPECTATION
    return Order.get_or_none(
        (Order.taxi_id == taxi_id) &
        (Order.status.in_([OrderStatus.GENERATED, OrderStatus.ACCEPTED, OrderStatus.EXPECTATION, OrderStatus.TRIP]))
    )


async def get_all_taxis():
    taxis = Taxi.select()
    return taxis


async def get_all_taxis_with_child_seat():
    return Taxi.select().where(Taxi.child_seat == True)


def get_generated_orders():
    orders = Order.select().where(Order.status == 'GENERATED')
    return orders


def get_order_by_id(order_id):
    try:
        return Order.get(Order.id == order_id)
    except Order.DoesNotExist:
        return None




def get_blocked_taxis_for_user(user_id):
    user = User.get(User.user_id == user_id)
    return json.loads(user.blocked_taxis)

def get_blocked_users_for_taxi(taxi_id):
    taxi = Taxi.get(Taxi.user_id == taxi_id)
    return json.loads(taxi.blocked_users)


def get_order_by_user_id(user_id):
    return Order.get_or_none((Order.user_id == user_id) & (Order.status == OrderStatus.GENERATED))

def get_delivery_by_user_id(user_id):
    last_delivery = (
        Delivery
        .select()
        .where((Delivery.user_id == user_id) & (Delivery.status == DeliveryStatus.GENERATED))
        .order_by(Delivery.id.desc())
        .get_or_none()
    )
    return last_delivery

def get_delivery_by_id(order_id):
    try:
        return Delivery.get(Delivery.id == order_id)
    except Delivery.DoesNotExist:
        return None
    
def get_delivery_by_taxi_id(taxi_id):
    # Получаем заказ для такси, где статус заказа в прогрессе выполнения
    return Delivery.get_or_none(
        (Delivery.taxi_id == taxi_id) &
        (Delivery.status.in_([DeliveryStatus.GENERATED, DeliveryStatus.ACCEPTED, DeliveryStatus.GET_PACKAGE, DeliveryStatus.LEAVING, DeliveryStatus.IN_PLACE ]))
    )


def has_orders(user_id):
    # Проверяем наличие заказов для пользователя с заданным user_id
    # Теперь мы также проверяем, чтобы статус был GENERATED, ACCEPTED или EXPECTATION
    orders_count = Order.select().where(
        (Order.user_id == user_id) &
        (Order.status.in_([OrderStatus.GENERATED, OrderStatus.ACCEPTED, OrderStatus.EXPECTATION, OrderStatus.TRIP, ]))
    ).count()
    return orders_count > 0

def has_delivery_orders(user_id):
    # Проверяем наличие заказов для пользователя с заданным user_id
    # Теперь мы также проверяем, чтобы статус был GENERATED, ACCEPTED или EXPECTATION
    orders_count = Delivery.select().where(
        (Delivery.user_id == user_id) &
        (Delivery.status.in_([DeliveryStatus.GENERATED, DeliveryStatus.ACCEPTED, DeliveryStatus.GET_PACKAGE, DeliveryStatus.LEAVING, DeliveryStatus.IN_PLACE ]))
    ).count()
    return orders_count > 0


def get_sent_messages(order_id):
    return [(msg.user_id, msg.message_id) for msg in Order.get(Order.id == order_id).sent_messages]

def delivery_get_sent_messages(order_id):
    return [(msg.user_id, msg.message_id) for msg in Delivery.get(Delivery.id == order_id).sent_messages]


async def get_active_orders_by_user_id(user_id):
    # Получаем список заказов для пользователя с заданным user_id и с нужным статусом
    orders = Order.select().where(
        (Order.user_id == user_id) &
        (Order.status.in_([OrderStatus.GENERATED, OrderStatus.ACCEPTED, OrderStatus.EXPECTATION, OrderStatus.TRIP]))
    )
    return orders

async def get_active_delivery_by_user_id(user_id):
    # Получаем список заказов для пользователя с заданным user_id и с нужным статусом
    orders = Delivery.select().where(
        (Delivery.user_id == user_id) &
        (Delivery.status.in_([DeliveryStatus.GENERATED, DeliveryStatus.ACCEPTED, DeliveryStatus.GET_PACKAGE, DeliveryStatus.LEAVING, DeliveryStatus.IN_PLACE ]))
    )
    return orders


async def get_orders_by_user_id(user_id):
    # Получаем список заказов для пользователя с заданным user_id
    orders = Order.select().where(Order.user_id == user_id)

    # Создаем список кортежей с координатами геопозиций заказов, где они доступны
    locations = [
        (order.first_latitude, order.first_longitude) if order.first_latitude and order.first_longitude else None
        for order in orders
    ]
    locations += [
        (order.second_latitude, order.second_longitude) if order.second_latitude and order.second_longitude else None
        for order in orders
    ]

    # Получаем список адресов для всех координат
    addresses = []
    for location in locations:
        if location:
            address = await get_address_from_coordinates(*location)
            addresses.append(address)
        else:
            addresses.append(None)

    # Проверяем наличие геопозиций в каждом заказе и присваиваем адреса и стоимость при их наличии
    for order, first_address, second_address in zip(orders, addresses[:len(orders)], addresses[len(orders):]):
        order.first_address = first_address
        order.second_address = second_address

        if first_address and second_address:
            first_location = (order.first_latitude, order.first_longitude)
            second_location = (order.second_latitude, order.second_longitude)
            distance = geodesic(first_location, second_location).kilometers
            order.distance = distance

    return list(orders)


async def get_address_from_coordinates(lat, lon):
    location = await geolocator.reverse([lat, lon], exactly_one=True)
    return location.address


def get_all_unique_users():
    user_ids = set()
    for user in User.select():
        user_ids.add(user.user_id)
    for taxi in Taxi.select():
        user_ids.add(taxi.user_id)
    return user_ids


def get_all_drivers():
    user_ids = set()
    for taxi in Taxi.select():
        user_ids.add(taxi.user_id)
    return user_ids


def get_all_passengers():
    user_ids = set()
    for user in User.select():
        user_ids.add(user.user_id)
    return user_ids


def get_all_passengers_null():
    user_ids = set()
    for user in User.select().where(User.rating.is_null()):
        user_ids.add(user.user_id)
    return user_ids


def get_free_taxis_count():
    return Taxi.select().where(
        (Taxi.is_busy == False) & (Taxi.is_active == True) & (Taxi.admin_deactivated == False) & (
                Taxi.shift == True)).count()

def get_free_deliveries_count():
    return Taxi.select().where(
        (Taxi.is_busy == False) & (Taxi.delivery_active == True) & (Taxi.admin_deactivated == False)).count()


def get_sent_item_by_order(order):
    try:
        sent_item = SentItem.select().where(SentItem.order == order).get()
    except SentItem.DoesNotExist:
        return None
    return sent_item

def delivery_get_sent_item_by_order(order):
    try:
        sent_item = SentDeliveryItem.select().where(SentDeliveryItem.order == order).get()
    except SentDeliveryItem.DoesNotExist:
        return None
    return sent_item

def get_delivery_orders_by_taxi_id(taxi_id):
    try:
        return Delivery.select().where((Delivery.busy_by == taxi_id) & (Delivery.status.not_in([DeliveryStatus.CANCELED, DeliveryStatus.COMPLETED])))
    except Delivery.DoesNotExist:
        return None

def get_delivery_orders_buttons(taxi_id):
    delivery_orders = get_delivery_orders_by_taxi_id(taxi_id)
    if delivery_orders:
        return [InlineKeyboardButton(f'🔅 Заказ #{order.id}', callback_data=f'delivery_order_{order.id}') for order in
                delivery_orders]
    return []

def get_delivery_orders_for_user(user_id):
    try:
        # return Delivery.select().where((Delivery.user_id == user_id) & (Delivery.status != DeliveryStatus.CANCELED)) 
        return Delivery.select().where((Delivery.user_id == user_id) & (Delivery.status.not_in([DeliveryStatus.CANCELED, DeliveryStatus.COMPLETED])))
    except Delivery.DoesNotExist:
        return None

def get_delivery_orders_user(user_id):
    delivery_orders = get_delivery_orders_for_user(user_id)
    if delivery_orders:
        return [InlineKeyboardButton(f'🔅 Заказ #{order.id}', callback_data=f'user_delivery_orders_{order.id}') for order
                in
                delivery_orders]
    return []


def get_deferred_orders_by_taxi_id(taxi_id):
    try:
        return Order.select().where(Order.deferred == True, Order.deferred_by == taxi_id)
    except Order.DoesNotExist:
        return None


def get_deferred_orders_for_user(user_id):
    try:
        return Order.select().where((Order.user_id == user_id) & (Order.deferred == True))
    except Order.DoesNotExist:
        return None


def get_deferred_orders_buttons(taxi_id):
    deferred_orders = get_deferred_orders_by_taxi_id(taxi_id)
    if deferred_orders:
        return [InlineKeyboardButton(f'🔅 Заказ #{order.id}', callback_data=f'deferred_order_{order.id}') for order in
                deferred_orders]
    return []


def get_deferred_orders_user(user_id):
    deferred_orders = get_deferred_orders_for_user(user_id)
    if deferred_orders:
        return [InlineKeyboardButton(f'🔅 Заказ #{order.id}', callback_data=f'user_deferred_orders_{order.id}') for order
                in
                deferred_orders]
    return []


def get_taxi_by_phone(phone_number):
    try:
        return Taxi.get(Taxi.phone == phone_number)
    except Taxi.DoesNotExist:
        return None


def get_passenger_by_phone(phone: str):
    try:
        return User.get(User.phone == phone)
    except User.DoesNotExist:
        return None
