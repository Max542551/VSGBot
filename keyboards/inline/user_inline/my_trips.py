from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Order
from database.get_to_db import get_taxi
from loader import bot, dp
from states.order_states import OrderStatus


# Нажатие на кнопку "Мои поездки"
@dp.callback_query_handler(lambda c: c.data == 'info')
async def my_trips(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    orders = Order.select().where(Order.user_id == user_id)

    if orders:
        markup = InlineKeyboardMarkup()

        for order in orders:
            status = "Выполнен" if order.status == OrderStatus.COMPLETED else "Не выполнен"
            markup.add(InlineKeyboardButton(f"Заказ №{order.id} - {status}", callback_data=f"order_info_{order.id}"))

        await bot.send_message(user_id, "Ваши поездки:", reply_markup=markup)
    else:
        await bot.send_message(user_id, "У вас еще не было поездок.")


# Нажатие на кнопку с конкретным заказом
@dp.callback_query_handler(lambda c: c.data.startswith('order_info_'))
async def order_info(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[2])
    order = Order.get_by_id(order_id)
    taxi = await get_taxi(order.taxi_id)

    if order:
        message = f"""
        Информация о заказе №{order.id}:
        Таксист: {taxi.name if taxi else 'Не определен'}
        Номер водителя: {taxi.phone if taxi else 'Не определен'}
        Адрес отправление {order.first_address}
        Адрес назначения {order.second_address}
        Статус: {"Выполнен" if order.status == OrderStatus.COMPLETED else "Не выполнен"}
        Стоимость: {order.cost}
        Оценка: {order.rating}
        """
        await bot.send_message(callback_query.from_user.id, message)
    else:
        await bot.send_message(callback_query.from_user.id, "Не удалось найти информацию о заказе.")
