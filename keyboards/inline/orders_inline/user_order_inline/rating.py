import json

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config_data.config import group_id, block_words
from database.database import Delivery, Order, User, Taxi
from database.get_to_db import get_taxi, get_user, get_order_by_id
from loader import bot, dp
from states.delivery_states import DeliveryStatus
from states.order_states import OrderStatus
from states.taxi_states import BanDriverStates


def get_rating_keyboard(order_id):
    keyboard = InlineKeyboardMarkup()

    rating_buttons = [
        InlineKeyboardButton(emoji, callback_data=f"rate_{order_id}_{rating}")
        for rating, emoji in zip(range(1, 6), ["1", "2", "3", "4", "5"])
    ]

    keyboard.row(*rating_buttons)
    block_driver_button = InlineKeyboardButton("🚫 Заблокировать водителя 🚫", callback_data=f"ban_driver_{order_id}")
    keyboard.add(block_driver_button)

    return keyboard


def get_user_rating_keyboard(user_id, order_id):
    keyboard = InlineKeyboardMarkup()

    rating_buttons = [
        InlineKeyboardButton(emoji, callback_data=f"userrate_{user_id}_{rating}")
        for rating, emoji in zip(range(1, 6), ["1", "2", "3", "4", "5"])
    ]

    keyboard.row(*rating_buttons)
    ban_button = InlineKeyboardButton("🚫 Заблокировать пассажира 🚫", callback_data=f"ban_passenger_{order_id}")
    keyboard.add(ban_button)

    return keyboard


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('rate'))
async def rate_order(callback_query: types.CallbackQuery):
    _, order_id, rating = callback_query.data.split("_", 2)
    order_id, rating = int(order_id), int(rating)

    order = Order.get_by_id(order_id)
    order.rating = rating
    order.save()

    taxi = await get_taxi(order.taxi_id)
    orders = Order.select().where(Order.taxi_id == taxi.user_id, Order.status != OrderStatus.CANCELED)
    deliveries = Delivery.select().where(Delivery.taxi_id == taxi.user_id, Delivery.status != DeliveryStatus.CANCELED)
    rated_orders = [order for order in orders if order.rating is not None]
    rated_deliveries = [delivery for delivery in deliveries if delivery.rating is not None]
    if rated_orders or rated_deliveries:
        raiting_list = rated_orders + rated_deliveries 
        total_rating = sum([order.rating for order in raiting_list])
        taxi.rating = round(total_rating / len(raiting_list), 2)
    else:
        taxi.rating = rating
    taxi.save()

    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(text="😊 Спасибо за оценку!", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    # await bot.send_message(taxi.user_id, f"📄 Заказ №<b>{order_id}</b> был оценен.\n\n"
    #                                      f"📈 Ваш рейтинг обновлен!", parse_mode='html')


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('userrate'))
async def rate_user(callback_query: types.CallbackQuery):
    _, user_id, rating = callback_query.data.split("_", 2)
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


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('ban_driver_'))
async def process_ban_driver_callback(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = callback_query.data.split('_')[-1]

    await state.update_data(order_id=order_id, user_id=callback_query.from_user.id)
    await BanDriverStates.waiting_for_reason.set()

    cancel_button = InlineKeyboardButton("🙅‍♂️ Я передумал", callback_data="cancel_ban_process")
    markup = InlineKeyboardMarkup().add(cancel_button)

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "✍️ Пожалуйста, укажите причину бана водителя: ",
                           reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data == 'cancel_ban_process', state=BanDriverStates.waiting_for_reason)
async def process_cancel_ban_driver(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    order_id = user_data['order_id']

    await bot.answer_callback_query(callback_query.id, text="Процесс бана отменен.")
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=f"👌 Процесс бана отменен.")

    await state.finish()


@dp.message_handler(state=BanDriverStates.waiting_for_reason, content_types=types.ContentTypes.TEXT)
async def process_ban_driver_reason(message: types.Message, state: FSMContext):
    if message.text in block_words:
        await message.answer('Введите корректную причину')
        return
    
    reason = message.text
    user_data = await state.get_data()
    order_id = user_data['order_id']
    user_id = user_data['user_id']
    order = get_order_by_id(order_id)
    user = await get_user(user_id)
    taxi = await get_taxi(order.taxi_id)

    try:
        # Получаем информацию о заказе
        order = Order.get(Order.id == order_id)

        # Добавляем водителя в список заблокированных таксистов пассажира
        blocked_taxis = json.loads(user.blocked_taxis)
        if order.taxi_id not in blocked_taxis:
            blocked_taxis.append(order.taxi_id)
            user.blocked_taxis = json.dumps(blocked_taxis)
            user.save()

        # await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


        # Отправляем подтверждение пассажиру
        await bot.send_message(user_id,
                               f"✅ Водитель {taxi.name} заблокирован.")

        await bot.send_message(group_id,
                               f"🚫 Пассажир <b>{user.name}</b> заблокировал водителя <b>{taxi.name}</b> по причине: <b>{reason}</b>.", parse_mode='html')

    except Order.DoesNotExist:
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
