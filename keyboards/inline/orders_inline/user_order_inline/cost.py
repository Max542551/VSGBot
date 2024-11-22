from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def cost_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Указать сумму", callback_data="specify_amount"),
               InlineKeyboardButton("Цена такси", callback_data="request_offers"))
    return markup
