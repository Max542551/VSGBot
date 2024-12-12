import json
from aiogram.dispatcher import FSMContext
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config_data.config import group_id

from database.database import Delivery, Order, Taxi, User
from database.get_to_db import get_delivery_by_id, get_taxi, get_user
from keyboards.inline.orders_inline.user_order_inline import rating
from loader import dp, bot
from states.delivery_states import BanCustomerStates, BanDeliveryStates, DeliveryStatus
from states.order_states import OrderStatus

def delivery_get_rating_keyboard(order_id):
    keyboard = InlineKeyboardMarkup()

    rating_buttons = [
        InlineKeyboardButton(emoji, callback_data=f"deliveryrate_{order_id}_{rating}")
        for rating, emoji in zip(range(1, 6), ["1", "2", "3", "4", "5"])
    ]

    keyboard.row(*rating_buttons)
    block_driver_button = InlineKeyboardButton("🚫 Заблокировать доставщика 🚫", callback_data=f"ban_delivery_{order_id}")
    keyboard.add(block_driver_button)

    return keyboard

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('delivery_rate'))
async def rate_order(callback_query: types.CallbackQuery):
    _, _, order_id, rating = callback_query.data.split("_", 3)
    order_id, rating = int(order_id), int(rating)

    order = Delivery.get_by_id(order_id)
    order.rating = rating
    order.save()

    taxi = await get_taxi(order.taxi_id)
    orders = Order.select().where(Order.taxi_id == taxi.user_id, Order.status != OrderStatus.CANCELED)
    deliveries = Delivery.select().where(Delivery.taxi_id == taxi.user_id, Delivery.status != DeliveryStatus.CANCELED)
    rated_orders = [order for order in orders if order.rating is not None]
    rated_deliveries = [delivery for delivery in deliveries if delivery.rating is not None]
    if rated_orders or rated_deliveries:
        raiting_list = rated_orders.extend(rated_deliveries)
        total_rating = sum([order.rating for order in raiting_list])
        taxi.rating = round(total_rating / len(rated_orders), 2)
    else:
        taxi.rating = rating
    taxi.save()

    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(text="😊 Спасибо за оценку!", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    await bot.send_message(taxi.user_id, f"📄 Заказ №<b>{order_id}</b> был оценен.\n\n"
                                         f"📈 Ваш рейтинг обновлен!", parse_mode='html')
    
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('ban_delivery'))
async def process_ban_delivery_callback(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = callback_query.data.split('_')[-1]

    await state.update_data(order_id=order_id, user_id=callback_query.from_user.id)
    await BanDeliveryStates.waiting_for_reason.set()

    cancel_button = InlineKeyboardButton("🙅‍♂️ Я передумал", callback_data="cancel_ban_process")
    markup = InlineKeyboardMarkup().add(cancel_button)

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "✍️ Пожалуйста, укажите причину бана водителя: ",
                           reply_markup=markup)


@dp.message_handler(state=BanDeliveryStates.waiting_for_reason, content_types=types.ContentTypes.TEXT)
async def process_ban_driver_reason(message: types.Message, state: FSMContext):
    reason = message.text
    user_data = await state.get_data()
    order_id = user_data['order_id']
    user_id = user_data['user_id']
    order = get_delivery_by_id(order_id)
    user = await get_user(user_id)
    taxi = await get_taxi(order.taxi_id)

    try:
        # Получаем информацию о заказе
        order = Delivery.get(Delivery.id == order_id)

        # Добавляем водителя в список заблокированных таксистов пассажира
        blocked_taxis = json.loads(user.blocked_taxis)
        if order.taxi_id not in blocked_taxis:
            blocked_taxis.append(order.taxi_id)
            user.blocked_taxis = json.dumps(blocked_taxis)
            user.save()

        # await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


        # Отправляем подтверждение пассажиру
        await bot.send_message(user_id,
                               f"✅ Доставщик {taxi.name} заблокирован.")

        await bot.send_message(group_id,
                               f"🚫 Заказчик <b>{user.name}</b> заблокировал водителя <b>{taxi.name}</b> по причине: <b>{reason}</b>.", parse_mode='html')

    except Delivery.DoesNotExist:
        await bot.send_message(user_id, "Ошибка: заказ не найден.")
    except User.DoesNotExist:
        await bot.send_message(user_id, "Ошибка: пассажир не найден.")
    except Taxi.DoesNotExist:
        await bot.send_message(user_id, "Ошибка: водитель не найден.")
    except Exception as e:
        print(f"⚠️ Ошибка при обработке запроса на бан водителя: {e}")
        await bot.send_message(user_id, "Произошла ошибка при попытке забанить водителя.")
    finally:
        # Завершаем состояние
        await state.finish()
    
def delivery_rate_user_keyboard(user_id, order_id):
    keyboard = InlineKeyboardMarkup()

    rating_keyboards = [
        InlineKeyboardButton(emoji, callback_data=f"customer_rate_{user_id}_{rating}")
        for rating, emoji in zip(range(1, 6), ["1", "2", "3", "4", "5"])
    ]
    keyboard.row(*rating_keyboards)
    block_customer_button = InlineKeyboardButton(text="🚫 Заблокировать заказчика 🚫", callback_data=f"ban_customer_{order_id}")
    keyboard.add(block_customer_button)
    return keyboard

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("customer_rate"))
async def rate_customer(callback_query: types.CallbackQuery):
    _, _, user_id, rating = callback_query.data.split("_", 3)
    user_id, rating = int(user_id), int(rating)

    user = await get_user(user_id)
    if user.rating is None:
        user.rating = rating
    else:
        # Измените это на подходящую для вас логику вычисления среднего рейтинга
        user.rating = (user.rating + rating) / 2
    user.save()

    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(text="😊 Спасибо за оценку пассажира!", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('deliveryrate'))
async def rate_user(callback_query: types.CallbackQuery):
    _, order_id, rating = callback_query.data.split("_", 2)
    order_id, rating = int(order_id), int(rating)

    order = Delivery.get_by_id(order_id)
    order.rating = rating
    order.save()

    taxi = await get_taxi(order.taxi_id)
    orders = Delivery.select().where(Delivery.taxi_id == taxi.user_id, Delivery.status != DeliveryStatus.CANCELED)
    rated_orders = [order for order in orders if order.rating is not None]
    if rated_orders:
        total_rating = sum([order.rating for order in rated_orders])
        taxi.rating = round(total_rating / len(rated_orders), 2)
    else:
        taxi.rating = rating
    taxi.save()

    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(text="😊 Спасибо за оценку!", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    await bot.send_message(taxi.user_id, f"📄 Заказ №<b>{order_id}</b> был оценен.\n\n"
                                         f"📈 Ваш рейтинг обновлен!", parse_mode='html')

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('ban_customer'))
async def process_ban_customer_callback(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = callback_query.data.split('_')[-1]

    await state.update_data(order_id=order_id, taxi_id=callback_query.from_user.id)
    await BanCustomerStates.waiting_for_reason.set()

    cancel_button = InlineKeyboardButton("🙅‍♂️ Я передумал", callback_data="cancel_ban_process")
    markup = InlineKeyboardMarkup().add(cancel_button)

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "✍️ Пожалуйста, укажите причину бана пассажира: ",
                           reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data == 'cancel_ban_process', state=BanCustomerStates.waiting_for_reason)
async def process_cancel_ban(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    order_id = user_data['order_id']

    await bot.answer_callback_query(callback_query.id, text="Процесс бана отменен.")
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=f"👌 Процесс бана отменен. Заказ #{order_id} продолжается.")

    await state.finish()

@dp.message_handler(state=BanCustomerStates.waiting_for_reason, content_types=types.ContentTypes.TEXT)
async def process_ban_reason(message: types.Message, state: FSMContext):
    reason = message.text
    user_data = await state.get_data()
    order_id = user_data['order_id']
    taxi_id = user_data['taxi_id']
    order = get_delivery_by_id(order_id)
    user = await get_user(order.user_id)
    taxi = await get_taxi(taxi_id)

    try:
        # Получаем информацию о заказе
        order = Delivery.get(Delivery.id == order_id)

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
                                   f"✅ Заказчик {user.name} заблокирован. Заказ #{order_id} отменен по причине: {reason}.")

            await bot.send_message(group_id,
                                   f"🚫 Водитель <b>{taxi.name}</b> заблокировал заказчика <b>{user.name}</b> по причине: <b>{reason}</b>.",
                                   parse_mode='html')

            await bot.send_message(order.user_id, f"😒 Ваш заказ № {order.id} был отменен доставщиком.")
            # Обновляем статус заказа на 'canceled'
            order.status = DeliveryStatus.CANCELED
            order.save()
        else:
            # Отправляем подтверждение водителю
            await bot.send_message(taxi_id,
                                   f"✅ Заказчик {user.name} заблокирован.")

            await bot.send_message(group_id,
                                   f"🚫 Водитель <b>{taxi.name}</b> заблокировал заказчика <b>{user.name}</b> по причине: <b>{reason}</b>.",
                                   parse_mode='html')

    # except DoesNotExist:
    #     await bot.send_message(taxi_id, "Ошибка: заказ не найден.")
    except Exception as e:
        print(f"⚠️ Ошибка при обработке запроса на бан пассажира: {e}")
        await bot.send_message(taxi_id, "Произошла ошибка при попытке забанить пассажира.")

    finally:
        # Завершаем состояние
        await state.finish()