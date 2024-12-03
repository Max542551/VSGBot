from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.add_to_db import save_sent_messages
from database.database import Taxi
from database.delite_from_db import remove_taxi
from database.get_to_db import get_all_taxis, get_all_taxis_with_child_seat, get_user, get_blocked_users_for_taxi, get_blocked_taxis_for_user
from keyboards.inline.orders_inline.time_key import get_time_keyboard
from keyboards.inline.taxi_inline.reply_accept_the_order import order_acceptance_keyboard, order_acceptance_keyboard_def
from loader import bot, dp


async def notify_taxi_drivers(order, first_address, second_address):
    user = await get_user(order.user_id)
    cost = "Ждет предложения" if order.cost is None else f"{order.cost} руб"
    rating_pass = round(user.rating, 2) if user.rating else "Еще нет рейтинга"
    message_text = f"❗️<b>Новый заказ</b>❗️ #{order.id}\n\n\n" \
                   f"🙋‍♂️ <b>Имя пассажира:</b> {user.name}\n\n" \
                   f"👥️ <b>Количество пассажиров:</b> {order.count_passanger}\n\n" \
                   f"📈 <b>Рейтинг пассажира:</b> {rating_pass}\n\n" \
                   f"📱 <b>Номер телефона клиента:</b> {'+' + user.phone}\n\n\n" \
                   f"🟢️ <b>Откуда:</b> {first_address}\n\n" \
                   f"🔴 <b>Куда:</b> {second_address}\n\n" \
                   f"💰 <b>Стоимость:</b> {cost}\n\n" \
                   f"💵 <b>Оплата:</b> {order.payment_method}\n\n" \
                   f"👶 <b>Детское кресло:</b> {order.child_seat}\n\n\n" \
                   f"💭 Комментарий к заказу: <b>{order.comment}</b>"

    child_seat_needed = order.child_seat == "Нужны"
    taxis = Taxi.select().where(Taxi.child_seat == child_seat_needed) if child_seat_needed else Taxi.select()
    sent_messages = []

    if order.cost is None:
        accept_keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton('💰 Предложить цену', callback_data=f'order_propose_price_{order.id}')
        )
    else:
        accept_keyboard = order_acceptance_keyboard(order)

    blocked_taxis = get_blocked_taxis_for_user(order.user_id)

    for taxi in taxis:
        if taxi.user_id in blocked_taxis:
            continue

        blocked_users = get_blocked_users_for_taxi(taxi.user_id)

        if order.user_id in blocked_users:
            continue

        if taxi.is_active and taxi.shift and not taxi.admin_deactivated:
            if taxi.is_busy:
                try:
                    time_keyboard = await get_time_keyboard(order.id)
                    message = await bot.send_message(chat_id=taxi.user_id, text=message_text,
                                               reply_markup=time_keyboard,
                                               parse_mode='html')
                    sent_messages.append((taxi.user_id, message.message_id))
                except Exception as e:
                    print(f"⚠️ Ошибка при отправке сообщения таксисту {taxi.user_id}: {e}")
            else:
                try:
                    message = await bot.send_message(chat_id=taxi.user_id, text=message_text,
                                               reply_markup=accept_keyboard,
                                               parse_mode='html')
                    sent_messages.append((taxi.user_id, message.message_id))
                except Exception as e:
                    print(f"⚠️ Ошибка при отправке сообщения таксисту {taxi.user_id}: {e}")

                    if "Forbidden: bot was blocked by the user" in str(e):
                        success = remove_taxi(taxi.user_id)
                        if success:
                            print(f"✅ Таксист с ID {taxi.user_id} был успешно удалён из базы данных")
        elif taxi.is_watching:
            try:
                await bot.send_message(chat_id=taxi.user_id, text=f'❗️<b>Новый заказ</b> #{order.id}',
                                 parse_mode='html')
            except Exception as e:
                print(f"⚠️ Ошибка при отправке сообщения таксисту {taxi.user_id}: {e}")

                if "Forbidden: bot was blocked by the user" in str(e):
                    success = remove_taxi(taxi.user_id)
                    if success:
                        print(f"✅ Таксист с ID {taxi.user_id} был успешно удалён из базы данных")

    save_sent_messages(order.id, sent_messages)



from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.add_to_db import save_sent_messages
from database.delite_from_db import remove_taxi
from database.get_to_db import get_all_taxis, get_all_taxis_with_child_seat, get_user
from keyboards.inline.taxi_inline.reply_accept_the_order import order_acceptance_keyboard
from loader import bot


async def notify_taxi_drivers_deffer(order, first_address, second_address):
    user = await get_user(order.user_id)
    cost = "Ждет предложения" if order.cost is None else f"{order.cost} руб"
    rating_pass = round(user.rating, 2) if user.rating else "Еще нет рейтинга"
    message_text = f"❗❗️<b>ПРЕДЗАКАЗ</b> ❗❗#{order.id}\n\n\n" \
                   f"👥️ <b>Количество пассажиров:</b> {order.count_passanger}\n\n" \
                   f"🙋‍♂️ <b>Имя пассажира:</b> {user.name}\n\n" \
                   f"📈 <b>Рейтинг пассажира</b> {rating_pass}\n\n" \
                   f"📱 <b>Номер телефона клиента:</b> {'+' + user.phone}\n\n\n" \
                   f"🟢️ <b>Откуда:</b> {first_address}\n\n" \
                   f"🔴 <b>Куда:</b> {second_address}\n\n" \
                   f"💰 <b>Стоимость:</b> {cost}\n\n" \
                   f"💵 <b>Оплата:</b> {order.payment_method}\n\n" \
                   f"👶 <b>Детское кресло:</b> {order.child_seat}\n\n\n" \
                   f"💭 Комментарий к заказу: <b>{order.comment}</b>"

    child_seat_needed = order.child_seat == "Нужны"
    taxis = Taxi.select().where(Taxi.child_seat == child_seat_needed) if child_seat_needed else Taxi.select()
    sent_messages = []

    if order.cost is None:
        accept_keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton('💰 Предложить цену', callback_data=f'order_propose_price_{order.id}')
        )
    else:
        accept_keyboard = order_acceptance_keyboard_def(order)

    blocked_taxis = get_blocked_taxis_for_user(order.user_id)

    for taxi in taxis:
        if taxi.user_id in blocked_taxis:
            continue

        blocked_users = get_blocked_users_for_taxi(taxi.user_id)

        if order.user_id in blocked_users:
            continue

        if taxi.is_active and not taxi.admin_deactivated:
            if taxi.is_busy:
                try:
                    time_keyboard = await get_time_keyboard(order.id)
                    message = await bot.send_message(chat_id=taxi.user_id, text=message_text,
                                                     reply_markup=time_keyboard,
                                                     parse_mode='html')
                    sent_messages.append((taxi.user_id, message.message_id))
                except Exception as e:
                    print(f"⚠️ Ошибка при отправке сообщения таксисту {taxi.user_id}: {e}")
            else:
                try:
                    message = await bot.send_message(chat_id=taxi.user_id, text=message_text,
                                                     reply_markup=accept_keyboard,
                                                     parse_mode='html')
                    sent_messages.append((taxi.user_id, message.message_id))
                except Exception as e:
                    print(f"⚠️ Ошибка при отправке сообщения таксисту {taxi.user_id}: {e}")

                    if "Forbidden: bot was blocked by the user" in str(e):
                        success = remove_taxi(taxi.user_id)
                        if success:
                            print(f"✅ Таксист с ID {taxi.user_id} был успешно удалён из базы данных")

    save_sent_messages(order.id, sent_messages)


@dp.callback_query_handler(lambda c: c.data.startswith('donfirm_order_defer_'))
async def confirm_order_defer(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[3])
    confirm_keyboard = InlineKeyboardMarkup()
    confirm_keyboard.add(InlineKeyboardButton('ПРОДОЛЖИТЬ', callback_data=f'dorder_defer_{order_id}'))
    confirm_keyboard.add(InlineKeyboardButton('Отменить', callback_data='defancel'))
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text="ВНИМАНИЕ!!!! Вы принимаете ПРЕДЗАКАЗ, Вы уверены что внимательно ознакомились с карточкой и готовы выполнить её в указанное время?",
                                reply_markup=confirm_keyboard)


@dp.callback_query_handler(lambda c: c.data == 'defancel')
async def cancel_order_defer(callback_query: types.CallbackQuery):
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text="Вы отказались от принятия предзаказа.")
