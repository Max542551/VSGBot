from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.database import Delivery
from database.get_to_db import get_taxi
from loader import dp, bot
from states.delivery_states import DeliveryStatus

def delivery_get_rating_keyboard(order_id):
    keyboard = InlineKeyboardMarkup()

    rating_buttons = [
        InlineKeyboardButton(emoji, callback_data=f"delivery_rate_{order_id}_{rating}")
        for rating, emoji in zip(range(1, 6), ["1", "2", "3", "4", "5"])
    ]

    keyboard.row(*rating_buttons)
    block_driver_button = InlineKeyboardButton("🚫 Заблокировать доставщика 🚫", callback_data=f"ban_driver_{order_id}")
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