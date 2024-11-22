from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.add_to_db import save_sent_delivery_messages
from database.database import Delivery, Taxi
from database.delite_from_db import remove_taxi
from database.get_to_db import get_blocked_taxis_for_user, get_blocked_users_for_taxi, get_user
from keyboards.inline.orders_inline.time_key import get_time_keyboard
from keyboards.inline.delivery_inline.reply_accept_the_delivery import delivery_acceptance_keyboard
from loader import bot, dp

async def notify_delivery_drivers(order, first_address, second_address):
    print(order.cost)
    print(order.comment)
    user = await get_user(order.user_id)
    cost = "Ждет предложения" if order.cost == None else f"{order.cost} руб"
    # package_payment = "Оплачена" if order.delivery_payment is "delivery_paid" else "Не оплачена"
    rating_pass = round(user.rating, 2) if user.rating else "Еще нет рейтинга"
    package_price = f"💰 <b>Сколько стоит посылка:</b> {order.package_price}\n\n" if order.package_price else ""
    message_text = f"❗️<b>Новый заказ</b> #{order.id}\n\n\n" \
                   f"📈 <b>Рейтинг заказчика:</b> {rating_pass}\n\n" \
                   f"📱 <b>Номер телефона клиента:</b> {'+' + user.phone}\n\n\n" \
                   f"🟢️ <b>Откуда:</b> {first_address}\n\n" \
                   f"🔴 <b>Куда:</b> {second_address}\n\n" \
                   f"💰 <b>Стоимость:</b> {cost}\n\n" \
                   f"💵 <b>Оплата:</b> {order.payment_method}\n\n" \
                   f"📦 <b>Оплата посылки:</b> {order.package_payment}\n\n" \
                   f"{package_price}" \
                   f"💍 <b>Содержимое посылки</b> {order.package_content}\n\n" \
                   f"💭 Комментарий к заказу: <b>{order.comment}</b>"

    taxis = Taxi.select()
    sent_messages = []

    if order.cost is None:
        accept_keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton('💰 Предложить цену', callback_data=f'delivery_order_propose_price_{order.id}')
        )
    else:
        accept_keyboard = delivery_acceptance_keyboard(order)

    blocked_taxis = get_blocked_taxis_for_user(order.user_id)

    for taxi in taxis:
        if taxi.user_id in blocked_taxis:
            continue

        blocked_users = get_blocked_users_for_taxi(taxi.user_id)

        if order.user_id in blocked_users:
            continue

        if taxi.delivery_active and not taxi.admin_deactivated:
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

    save_sent_delivery_messages(order.id, sent_messages)
