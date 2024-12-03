from datetime import datetime
from peewee import *
from config_data.config import database
from states.delivery_states import DeliveryStatus
from states.order_states import OrderStatus


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    user_id = IntegerField(unique=True)
    name = CharField()
    phone = CharField()
    rating = FloatField(null=True)
    is_active = BooleanField(default=True)
    home_address = CharField(null=True)
    work_address = CharField(null=True)
    blocked_taxis = TextField(default='[]')  # Поле для хранения заблокированных таксистов


class Taxi(BaseModel):
    user_id = IntegerField(unique=True)
    name = CharField()
    phone = CharField()
    balance = IntegerField(default=100)
    car = CharField()
    color_car = CharField()
    registration_number = CharField()
    child_seat = BooleanField(default=False)
    rating = FloatField(default=0)
    is_active = BooleanField(default=True)
    shift = BooleanField(default=False)
    shift_count = IntegerField(default=0)
    admin_deactivated = BooleanField(default=False)
    is_busy = BooleanField(default=False)
    shift_start_time = DateTimeField(null=True)
    daily_order_count = IntegerField(default=0)  # Счетчик заказов за день
    daily_earnings = FloatField(default=0.0)  # Сумма заработка за день
    daily_order_sum = FloatField(default=0.0)  # Сумма заказов за текущий день
    delivery_active = BooleanField(default=False)
    is_watching = BooleanField(default=False)
    blocked_users = TextField(default='[]')  # Поле для хранения заблокированных пользователей


class Order(BaseModel):
    user_id = CharField()
    taxi_id = IntegerField(null=True)
    first_address = CharField()
    second_address = CharField(null=True)
    status = CharField(default=OrderStatus.GENERATED)
    count_passanger = IntegerField(default=0)
    cost = FloatField(null=True)
    child_seat = CharField(null=True)
    payment_method = CharField(null=True)
    comment = TextField(null=True)
    order_date = DateTimeField(default=datetime.now)
    rating = FloatField(null=True)
    deferred = BooleanField(default=False)
    deferred_by = IntegerField(null=True)


class Delivery(BaseModel):
    user_id = CharField()
    taxi_id = IntegerField(null=True)
    first_address = CharField()
    second_address = CharField(null=True)
    status = CharField(default=DeliveryStatus.GENERATED)
    delivery_date = CharField(null=True)
    package_content = CharField()
    cost = FloatField(null=True)
    package_payment = CharField()
    package_price = CharField(null=True)
    payment_method = CharField(null=True)
    comment = TextField(null=True)
    order_date = DateTimeField(default=datetime.now)
    rating = FloatField(null=True)
    busy_by = IntegerField(null=True)


class SentMessage(BaseModel):
    order = ForeignKeyField(Order, backref='sent_messages')
    user_id = IntegerField()
    message_id = IntegerField()


class SentDeliveryMessage(BaseModel):
    order = ForeignKeyField(Delivery, backref='sent_messages')
    user_id = IntegerField()
    message_id = IntegerField()


class SentItem(BaseModel):
    order = ForeignKeyField(Order, backref='sent_items')
    text_message_id = IntegerField(null=True)
    start_location_message_id = IntegerField(null=True)
    end_location_message_id = IntegerField(null=True)

class SentDeliveryItem(BaseModel):
    order = ForeignKeyField(Delivery, backref='sent_items')
    text_message_id = IntegerField(null=True)
    start_location_message_id = IntegerField(null=True)
    end_location_message_id = IntegerField(null=True)




User.create_table()
Taxi.create_table()
Order.create_table()
SentMessage.create_table()
SentDeliveryMessage.create_table()
SentItem.create_table()
Delivery.create_table()
SentDeliveryItem.create_table()
