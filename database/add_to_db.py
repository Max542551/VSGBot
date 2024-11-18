import json

from database.database import User, Taxi, Order, SentMessage, SentItem


def add_user(user_id, name, phone):
    User.create(user_id=user_id, name=name, phone=phone)


def add_taxi(user_id, name, phone, car, color_car, registration_number, child_seat):
    Taxi.create(user_id=user_id, name=name, phone=phone, car=car, color_car=color_car,
                registration_number=registration_number, child_seat=child_seat)


def add_sent_item(order, message_id, latitude=None, longitude=None):
    return SentItem.create(order=order, message_id=message_id, latitude=latitude, longitude=longitude)


def add_blocked_taxi_for_user(user_id, taxi_id):
    user = User.get(User.user_id == user_id)
    blocked_taxis = json.loads(user.blocked_taxis)
    if taxi_id not in blocked_taxis:
        blocked_taxis.append(taxi_id)
        user.blocked_taxis = json.dumps(blocked_taxis)
        user.save()


def add_blocked_user_for_taxi(taxi_id, user_id):
    taxi = Taxi.get(Taxi.user_id == taxi_id)
    blocked_users = json.loads(taxi.blocked_users)
    if user_id not in blocked_users:
        blocked_users.append(user_id)
        taxi.blocked_users = json.dumps(blocked_users)
        taxi.save()


def create_order_in_db(order_data):
    Order.create(
        user_id=order_data["user_id"],
        first_address=order_data["first_address"],
        second_address=order_data["second_address"],
        child_seat=order_data["child_seat"],
        payment_method=order_data["payment_method"],
        comment=order_data["comment"],
        cost=order_data["cost"],
        deferred=order_data["deferred"],
        count_passanger=order_data["count_passanger"],
    )


def save_sent_messages(order_id, sent_messages):
    order = Order.get(Order.id == order_id)
    for user_id, message_id in sent_messages:
        SentMessage.create(order=order, user_id=user_id, message_id=message_id)


async def create_sent_item(order):
    sent_item = SentItem.get_or_none(order=order)
    if sent_item is None:
        sent_item = SentItem.create(order=order)
    return sent_item
