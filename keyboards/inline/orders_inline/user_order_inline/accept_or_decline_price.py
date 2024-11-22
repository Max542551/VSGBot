from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def accept_or_decline_price_keyboard(order, taxi_id, price, delivery="False"):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Принять", callback_data=f"acceptprice_{order.id}_{taxi_id}_{price}_{delivery}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"declineprice_{order.id}_{taxi_id}_{price}_{delivery}")
    )
    return keyboard