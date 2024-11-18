from aiogram import types


def comment_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        types.KeyboardButton("⛔️ Без комментариев")
    )
    return markup