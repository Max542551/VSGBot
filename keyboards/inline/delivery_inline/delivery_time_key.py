from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.get_to_db import get_delivery_by_id, get_taxi, get_order_by_id
from loader import dp, bot


async def delivery_get_time_keyboard(order_id):
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton("5 мин", callback_data=f"delivery_time_5_{order_id}"),
        InlineKeyboardButton("10 мин", callback_data=f"delivery_time_10_{order_id}"),
        InlineKeyboardButton("15 мин", callback_data=f"delivery_time_15_{order_id}")
    ]
    keyboard.add(*buttons)
    return keyboard


@dp.callback_query_handler(lambda call: call.data.startswith('delivery_time_'))
async def handle_time_selection(call: types.CallbackQuery):
    _, minutes, order_id = call.data.split('_')
    order = get_delivery_by_id(int(order_id))
    taxi = await get_taxi(call.from_user.id)

    accept_keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton('💰 Предложить цену', callback_data=f'delivery_order_propose_price_{order.id}')
    )

    await bot.send_message(call.from_user.id, f"❗️ После завершения заказа, предложите цену здесь для заказа {order.id}",
                        reply_markup=accept_keyboard)

    await bot.send_message(order.user_id,
                        f"🚖 Водитель <b>{taxi.name}</b> освободится через <b>{minutes}</b> минут и предложит вам свою цену.",
                        reply_markup=types.ReplyKeyboardRemove(), parse_mode="html") 