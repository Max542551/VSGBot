from aiogram import types
from aiogram.types import InlineKeyboardMarkup

from database.add_to_db import create_sent_item
from database.get_to_db import get_user, get_taxi, get_order_by_taxi_id, get_free_taxis_count, \
    get_deferred_orders_buttons
from database.update_to_db import update_sent_item
from keyboards.inline.orders_inline.taxi_order_inline.end_trip import get_end_trip_button
from keyboards.inline.orders_inline.taxi_order_inline.expectation_order import get_expectation_button
from keyboards.inline.orders_inline.taxi_order_inline.start_trip import get_start_trip_button
from keyboards.inline.taxi_inline.markup_main_taxi import markup_taxi
from states.order_states import OrderStatus


async def main_menu_taxi(message: types.Message):
    taxi_id = message.chat.id
    taxi = await get_taxi(taxi_id)
    free_taxis_count = get_free_taxis_count()

    # Поиск заказа для данного таксиста
    order = get_order_by_taxi_id(taxi_id)

    if order:
        user = await get_user(order.user_id)
        cost = "Ждет предложения" if order.cost is None else f"{order.cost} руб"

        # Вывод информации о заказе
        if order.status == OrderStatus.ACCEPTED:
            expectation_button = get_expectation_button(order.id)
            button = expectation_button
        elif order.status in [OrderStatus.EXPECTATION]:
            start_trip_button = get_start_trip_button(order.id)
            button = start_trip_button
        elif order.status in [OrderStatus.TRIP]:
            end_trip_button = get_end_trip_button(order.id)
            button = end_trip_button
        else:
            button = None

        response = await message.answer(f"📄 Информация о заказе № {order.id}:\n\n\n"
                                        f"🟢 <b>Адрес отправления:</b> {order.first_address}\n\n"
                                        f"🔴 <b>Адрес прибытия:</b> {order.second_address}\n\n\n"
                                        f"👥️ <b>Количество пассажиров:</b> {order.count_passanger}\n\n"
                                        f"🙋‍♂️ <b>Имя клиента:</b> {user.name}\n\n"
                                        f"📱 <b>Номер телефона клиента:</b> {'+'+user.phone}\n\n\n"
                                        f"💰 <b>Стоимость:</b> {cost}\n\n"
                                        f"💵 <b>Оплата:</b> {order.payment_method}\n\n"
                                        f"👶 <b>Детское кресло:</b> {order.child_seat}\n\n\n"
                                        f"💭 Комментарий к заказу: <b>{order.comment}</b>", reply_markup=button,
                                        parse_mode='html')
        sent_item = await create_sent_item(order)
        await update_sent_item(sent_item, text_message_id=response.message_id)



    else:
        # Если нет заказов, выводим приветственное сообщение
        await message.answer(f"👋 Привет, {taxi.name}!\n"
                             f"Удачи сегодня в работе! 🤗\n\n\n"
                             f"📋 Ваша личная карточка:\n\n\n"
                             f"📈 <b>Ваш рейтинг:</b> {round(taxi.rating, 2)}\n\n"
                             f"💵 <b>Ваш баланс:</b> {taxi.balance}\n\n"
                             f"🚖 <b>Марка автомобиля:</b> {taxi.car}\n\n"
                             f"🎨 <b>Цвет автомобиля:</b> {taxi.color_car}\n\n"
                             f"🎰 <b>Гос. Номер:</b> {taxi.registration_number}\n\n\n"
                             f"Сейчас свободных машин: {free_taxis_count}\n\n\n"
                             f"🎉 С 21.11.2023 Вы выполнили <b>{taxi.daily_order_count}</b> заказов на общую сумму: <b>{taxi.daily_earnings}</b> руб\n"
                             f"💵 <b>Сумма заказов за текущий день:</b> {taxi.daily_order_sum} руб",
                             reply_markup=markup_taxi(taxi), parse_mode='html')

        # Проверяем, есть ли отложенные заказы
        deferred_orders_buttons = get_deferred_orders_buttons(taxi.user_id)
        if deferred_orders_buttons:
            # Отправляем список отложенных заказов
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(*deferred_orders_buttons)
            await message.answer("❗ Отложенные заказы:", reply_markup=markup)
