from aiogram import types


def send_location_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="📍 Отправить местоположение", request_location=True)
    keyboard.add(button_geo)
    return keyboard
