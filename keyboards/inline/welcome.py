from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def generate_welcome_keyboard():
    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_btn_passenger = InlineKeyboardButton('🙋‍♂️ Пассажир', callback_data='passenger')
    inline_btn_taxi = InlineKeyboardButton('🚖 Водитель такси', callback_data='taxi')
    inline_btn_support = InlineKeyboardButton('👥 Связаться с поддержкой', callback_data='support')
    inline_btn_price = InlineKeyboardButton('💰 Стоимость поездок', callback_data='price')  # добавили новую кнопку
    inline_kb.add(inline_btn_passenger, inline_btn_taxi, inline_btn_price, inline_btn_support)
    return inline_kb