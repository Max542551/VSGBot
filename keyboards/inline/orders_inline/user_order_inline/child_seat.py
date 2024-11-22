from aiogram import types


def child_seat_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Нужно", callback_data="Нужно"),
        types.InlineKeyboardButton("❌ Не нужно", callback_data="Не нужно")
    )
    return markup
