from aiogram import types
from aiogram.types import InlineKeyboardMarkup

from database.add_to_db import create_sent_item, delivery_create_sent_item
from database.database import Delivery
from database.get_to_db import get_delivery_by_taxi_id, get_delivery_orders_buttons, get_user, get_taxi, get_order_by_taxi_id, get_free_taxis_count, \
    get_deferred_orders_buttons, get_shift_taxis_count
from database.update_to_db import update_sent_item
from keyboards.inline.delivery_inline.delivery_status_buttons.get_package_delivery import get_delivery_package_button
from keyboards.inline.delivery_inline.delivery_status_buttons.leaving_with_package import get_leaving_with_package_button
from keyboards.inline.orders_inline.taxi_order_inline.end_trip import get_end_trip_button
from keyboards.inline.orders_inline.taxi_order_inline.expectation_order import get_expectation_button
from keyboards.inline.orders_inline.taxi_order_inline.start_trip import get_start_trip_button
from keyboards.inline.taxi_inline.markup_main_taxi import markup_taxi
from states.delivery_states import DeliveryState, DeliveryStatus
from states.order_states import OrderStatus


async def main_menu_taxi(message: types.Message):
    taxi_id = message.chat.id
    taxi = await get_taxi(taxi_id)
    free_taxis_count = get_free_taxis_count()
    shift_taxis_count = get_shift_taxis_count()

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
        delivery = get_delivery_by_taxi_id(taxi_id)

        if delivery:
            user = await get_user(delivery.user_id)
            cost = "Ждет предложения" if delivery.cost is None else f"{delivery.cost} руб"

            # Вывод информации о заказе
            if delivery.status == DeliveryStatus.ACCEPTED:
                package_button = get_delivery_package_button(delivery.id)
                button = package_button
            elif delivery.status in [DeliveryStatus.GET_PACKAGE]:
                leaving_button = get_leaving_with_package_button(delivery.id)
                button = leaving_button
            elif delivery.status in [DeliveryStatus.LEAVING]:
                in_place_button = in_place_button(delivery.id)
                button = in_place_button
            else:
                button = None

            package_price = f"💰 <b>Сколько стоит посылка:</b> {delivery.package_price}\n\n" if delivery.package_price else ""
            response = await message.answer(f"📄 Информация о доставке №{delivery.id}:\n\n\n" \
                    f"🅰️ <b>Адрес отправления:</b> {delivery.first_address}\n\n" \
                    f"🅱️ <b>Адрес прибытия:</b> {delivery.second_address}\n\n\n" \
                    f"🙋‍♂️ <b>Имя клиента:</b> {user.name}\n\n" \
                    f"📱 <b>Номер телефона клиента:</b> {user.phone}\n\n\n" \
                    f"💰 <b>Стоимость:</b> {cost}\n\n" \
                    f"💵 <b>Оплата:</b> {delivery.payment_method}\n\n" \
                    f"📦 <b>Оплата посылки:</b> {delivery.package_payment}\n\n" \
                    f"{package_price}" \
                    f"💍 <b>Содержимое посылки</b> {delivery.package_content}\n\n" \
                    f"💭 Комментарий к заказу: <b>{delivery.comment}</b>", reply_markup=button, parse_mode='html')
            sent_item = await delivery_create_sent_item(delivery)
            await update_sent_item(sent_item, text_message_id=response.message_id)

        else:
            # Если нет заказов, выводим приветственное сообщение
            await message.answer(f"👋 Привет, {taxi.name}!\n"
                             f"Удачи сегодня в работе! 🤗\n\n\n"
                                f"📋 Ваша личная карточка: {taxi.phone}\n\n\n"
                                f"📈 <b>Ваш рейтинг:</b> {round(taxi.rating, 2)}\n\n"
                                f"💵 <b>Ваш баланс:</b> {taxi.balance}\n\n"
                                f"🚖 <b>Марка автомобиля:</b> {taxi.car}\n\n"
                                f"🎨 <b>Цвет автомобиля:</b> {taxi.color_car}\n\n"
                                f"🎰 <b>Гос. Номер:</b> {taxi.registration_number}\n\n\n"
                                f"Сейчас машин на линии: {shift_taxis_count}\n"
                                f"Сейчас свободных машин: {free_taxis_count}\n\n\n"
                                f"🎉 Вы выполнили <b>{taxi.daily_order_count}</b> заказов на общую сумму: <b>{taxi.daily_earnings}</b> руб\n"
                                f"💵 <b>Сумма заказов за текущий день:</b> {taxi.daily_order_sum} руб",
                                reply_markup=markup_taxi(taxi), parse_mode='html')

            # Проверяем, есть ли отложенные заказы
            deferred_orders_buttons = get_deferred_orders_buttons(taxi.user_id)
            if deferred_orders_buttons:
                # Отправляем список отложенных заказов
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(*deferred_orders_buttons)
                await message.answer("❗ Отложенные заказы:", reply_markup=markup)

            delivery_orders_buttons = get_delivery_orders_buttons(taxi.user_id)
            print(delivery_orders_buttons)
            if delivery_orders_buttons:
                markup = InlineKeyboardMarkup(row_width=1)
                markup.add(*delivery_orders_buttons)
                await message.answer("❗ Доставки:", reply_markup=markup)
