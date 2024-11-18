from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def markup_main():
    markup_main = InlineKeyboardMarkup(row_width=1)

    item1 = InlineKeyboardButton("❇️ Заказать такси", callback_data='order_a_taxi')
    item6 = InlineKeyboardButton("🏙 Предзаказ", callback_data='userdef_order')
    item2 = InlineKeyboardButton("📖 Мои поездки", callback_data='info')
    item7 = InlineKeyboardButton("📍 Мои адреса", callback_data='my_addresses')
    item3 = types.InlineKeyboardButton('👥 Поддержка', callback_data='support')
    item4 = InlineKeyboardButton('💰 Стоимость поездок', callback_data='price')
    item5 = InlineKeyboardButton('🚖 Стать водителем', callback_data='switch_to_taxi')
    markup_main.add(item1, item6, item2, item7, item3, item4, item5)

    return markup_main
