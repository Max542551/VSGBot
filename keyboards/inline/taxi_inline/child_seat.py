from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def reg_child_seat_keyboard():
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Да", callback_data='child_seat_yes'),
        InlineKeyboardButton("❌ Нет", callback_data='child_seat_no')
    )
    return kb
