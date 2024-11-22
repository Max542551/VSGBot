import json

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from peewee import DoesNotExist

from config_data.config import group_id
from database.database import Order
from database.get_to_db import get_order_by_id, get_taxi, get_user
from keyboards.inline.orders_inline.taxi_order_inline.end_trip import get_end_trip_button
from loader import bot, dp
from states.order_states import OrderStatus
from states.user_states import BanPassengerStates


def get_start_trip_button(order_id):
    markup = InlineKeyboardMarkup()
    start_trip_button = InlineKeyboardButton("🟢 Начать поездку 🟢", callback_data=f"order_start_trip_{order_id}")
    cancel_button = InlineKeyboardButton("❌ Пассажир не вышел ❌", callback_data=f"passenger_no_show_{order_id}")
    ban_button = InlineKeyboardButton("🚫 Заблокировать пассажира 🚫", callback_data=f"ban_passenger_{order_id}")
    markup.add(start_trip_button)
    markup.add(cancel_button)
    markup.add(ban_button)
    return markup


@dp.callback_query_handler(lambda c: c.data.startswith('order_start_trip_'))
async def process_start_trip(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = int(callback_query.data.split("_")[3])
    taxi_id = callback_query.from_user.id
    taxi = await get_taxi(taxi_id)

    order = get_order_by_id(order_id)
    if order is None:
        await bot.send_message(taxi_id, "Не удалось найти заказ.")
        return

    if order.taxi_id != taxi_id:
        await bot.send_message(taxi_id, "Этот заказ не принадлежит вам.")
        return

    if order.status == OrderStatus.CANCELED or order.status == OrderStatus.COMPLETED:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⛔️ Заказ был отменен."
        )
        return

    commission = 10  # 10р комиссия

    if taxi.balance < commission:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Недостаточно средств для поездки!\n\n")
        return

    if taxi.shift_count > 3:
        taxi.balance -= commission
        taxi.save()
        await bot.send_message(group_id,
                               f'🟢 Списана комиссия за заказ #{order.id} с <b>{taxi.name} {taxi.car} {taxi.registration_number}</b> - баланс {taxi.balance}',
                               parse_mode='html')
    else:
        await bot.send_message(group_id,
                               f'🟡 Заказ #{order.id}. У <b>{taxi.name} {taxi.car} {taxi.registration_number}</b> осталось {3 - taxi.shift_count} бесплатные поездки!',
                               parse_mode='html')

    order.status = OrderStatus.TRIP
    order.save()

    await bot.send_message(
        chat_id=order.user_id,
        text=f"🚕💨 Ваша поездка началась! Приятного пути. Пожалуйста пристегните ремни безопасности❤️"
    )

    await bot.edit_message_reply_markup(
        chat_id=taxi_id,
        message_id=callback_query.message.message_id,
        reply_markup=get_end_trip_button(order_id)
    )

    await bot.answer_callback_query(callback_query.id)
    await state.finish()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('ban_passenger_'))
async def process_ban_passenger_callback(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = callback_query.data.split('_')[-1]

    await state.update_data(order_id=order_id, taxi_id=callback_query.from_user.id)
    await BanPassengerStates.waiting_for_reason.set()

    cancel_button = InlineKeyboardButton("🙅‍♂️ Я передумал", callback_data="cancel_ban_process")
    markup = InlineKeyboardMarkup().add(cancel_button)

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "✍️ Пожалуйста, укажите причину бана пассажира: ",
                           reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data == 'cancel_ban_process', state=BanPassengerStates.waiting_for_reason)
async def process_cancel_ban(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    order_id = user_data['order_id']

    await bot.answer_callback_query(callback_query.id, text="Процесс бана отменен.")
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=f"👌 Процесс бана отменен. Заказ #{order_id} продолжается.")

    await state.finish()


@dp.message_handler(state=BanPassengerStates.waiting_for_reason, content_types=types.ContentTypes.TEXT)
async def process_ban_reason(message: types.Message, state: FSMContext):
    reason = message.text
    user_data = await state.get_data()
    order_id = user_data['order_id']
    taxi_id = user_data['taxi_id']
    order = get_order_by_id(order_id)
    user = await get_user(order.user_id)
    taxi = await get_taxi(taxi_id)

    try:
        # Получаем информацию о заказе
        order = Order.get(Order.id == order_id)

        # Добавляем запись о бане
        # Добавляем пассажира в список заблокированных пользователей таксиста
        blocked_users = json.loads(taxi.blocked_users)
        if order.user_id not in blocked_users:
            blocked_users.append(order.user_id)
            taxi.blocked_users = json.dumps(blocked_users)
            taxi.save()

        if order.status != "COMPLETED":
            taxi.is_busy = False
            taxi.save()

            # Отправляем подтверждение водителю
            await bot.send_message(taxi_id,
                                   f"✅ Пассажир {user.name} заблокирован. Заказ #{order_id} отменен по причине: {reason}.")

            await bot.send_message(group_id,
                                   f"🚫 Водитель <b>{taxi.name}</b> заблокировал пассажира <b>{user.name}</b> по причине: <b>{reason}</b>.",
                                   parse_mode='html')

            await bot.send_message(order.user_id, f"😒 Ваш заказ № {order.id} был отменен таксистом.")
            # Обновляем статус заказа на 'canceled'
            order.status = OrderStatus.CANCELED
            order.save()
        else:
            # Отправляем подтверждение водителю
            await bot.send_message(taxi_id,
                                   f"✅ Пассажир {user.name} заблокирован.")

            await bot.send_message(group_id,
                                   f"🚫 Водитель <b>{taxi.name}</b> заблокировал пассажира <b>{user.name}</b> по причине: <b>{reason}</b>.",
                                   parse_mode='html')

    except DoesNotExist:
        await bot.send_message(taxi_id, "Ошибка: заказ не найден.")
    except Exception as e:
        print(f"⚠️ Ошибка при обработке запроса на бан пассажира: {e}")
        await bot.send_message(taxi_id, "Произошла ошибка при попытке забанить пассажира.")

    finally:
        # Завершаем состояние
        await state.finish()
