from aiogram import types


def payment_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💵 Наличные", callback_data="Наличные"),
        types.InlineKeyboardButton("💳 Перевод", callback_data="Перевод")
    )
    return markup
