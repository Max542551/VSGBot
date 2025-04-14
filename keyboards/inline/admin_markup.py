from aiogram import types


def markup_admin():
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_broadcast = types.InlineKeyboardButton("📨 Общая рассылка", callback_data='admin_broadcast_all')
    btn_broadcast_drivers = types.InlineKeyboardButton("🚖 Рассылка водителям", callback_data='admin_broadcast_drivers')
    btn_broadcast_passengers = types.InlineKeyboardButton("👥 Рассылка пассажирам",
                                                          callback_data='admin_broadcast_passengers')
    btn_broadcast_passengers_null = types.InlineKeyboardButton("👥 Рассылка пассажирам NULL",
                                                          callback_data='nullpassengers')
    btn_toggle_driver = types.InlineKeyboardButton("📋 Карточка водителя", callback_data='toggle_driver')
    btn_toggle_passenger = types.InlineKeyboardButton("🧾 Карточка пассажира", callback_data='passtogle')
    btn_find_order = types.InlineKeyboardButton("🔍 Найти заказ", callback_data='find_order')
    btn_change_number_phone = types.InlineKeyboardButton("📞 Изменить номер телефона", callback_data='change_phone')
    btn_change_rating = types.InlineKeyboardButton("⭐ Изменить рейтинг", callback_data='change_rating')
    btn_busy_off = types.InlineKeyboardButton("🚖 Снять статус занят", callback_data='busy_off')

    inline_kb.add(btn_broadcast, btn_broadcast_drivers, btn_broadcast_passengers, btn_broadcast_passengers_null, btn_toggle_driver, btn_toggle_passenger, btn_find_order, btn_change_number_phone, btn_change_rating, btn_busy_off)
    return inline_kb
