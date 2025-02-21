from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def markup_taxi(taxi):
    taxi_shift = taxi.shift if taxi else False
    taxi_watching = taxi.is_watching if taxi else False
    delivery_active = taxi.delivery_active if taxi else False

    markup_taxi = InlineKeyboardMarkup(row_width=1)
    item1 = InlineKeyboardButton('🙋‍♂️ Стать пассажиром', callback_data='switch_to_passenger')
    item2 = InlineKeyboardButton('💵 Пополнить баланс', callback_data='top_up')
    item3 = InlineKeyboardButton('💰 Стоимость поездок', callback_data='price')
    item4 = InlineKeyboardButton('👥 Поддержка', callback_data='support')
    item6 = InlineKeyboardButton('👁️ Наблюдать' if not taxi_watching else '👁️ Прекратить наблюдение',
                                 callback_data='towatch')
    item8 = InlineKeyboardButton('🟢Беру доставку' if not delivery_active else '🔴Не беру доставку', callback_data="deliveryon")
    item7 = InlineKeyboardButton("🔄 Сбросить сумму заказов за день", callback_data="reset_daily_order_sum")
    item5 = InlineKeyboardButton('🔴 Завершить смену' if taxi_shift else '🟢 Начать смену', callback_data='change_shift')

    markup_taxi.add(item1, item2, item3, item4, item6, item8, item7, item5)

    return markup_taxi
