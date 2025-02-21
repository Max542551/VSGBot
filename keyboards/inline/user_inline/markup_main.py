from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def markup_main():
    markup_main = InlineKeyboardMarkup(row_width=1)

    item1 = InlineKeyboardButton("❇️ Заказать такси", callback_data='order_a_taxi')
    item2 = InlineKeyboardButton("🏙 Предзаказ", callback_data='userdef_order')
    item3 = InlineKeyboardButton("🚛 Заказать доставку", callback_data='user_delivery_order')
    item4 = InlineKeyboardButton("📖 Мои поездки", callback_data='info')
    item5 = InlineKeyboardButton("📍 Мои адреса", callback_data='my_addresses')
    item6 = InlineKeyboardButton('👥 Поддержка', callback_data='support')
    item7 = InlineKeyboardButton('💰 Стоимость поездок', callback_data='price')
    item8 = InlineKeyboardButton('🚖 Стать водителем', callback_data='switch_to_taxi')
    markup_main.add(item1, item2, item3, item4, item5, item6, item7, item8)

    return markup_main
