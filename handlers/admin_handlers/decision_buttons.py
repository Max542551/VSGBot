from aiogram import types


def make_decision_buttons(user_id: int, price: int) -> types.InlineKeyboardMarkup:
    inline_kb = types.InlineKeyboardMarkup()
    inline_btn_accept = types.InlineKeyboardButton('✅ Принять', callback_data=f"accept:{user_id}:{price}")
    inline_btn_reject = types.InlineKeyboardButton('❌ Отклонить', callback_data=f"reject:{user_id}:{price}")
    inline_kb.add(inline_btn_accept, inline_btn_reject)
    return inline_kb


def make_registration_decision_buttons(user_id: int) -> types.InlineKeyboardMarkup:
    inline_kb = types.InlineKeyboardMarkup()
    inline_btn_accept = types.InlineKeyboardButton('✅ Принять Регистрацию', callback_data=f"reg_accept:{user_id}")
    inline_btn_reject = types.InlineKeyboardButton('❌ Отклонить Регистрацию', callback_data=f"jer_regtaxi:{user_id}")
    inline_kb.add(inline_btn_accept, inline_btn_reject)
    return inline_kb
