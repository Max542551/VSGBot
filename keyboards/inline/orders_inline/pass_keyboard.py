from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def passengers_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=5)
    buttons = [InlineKeyboardButton(str(i), callback_data=f"passenger_{i}") for i in range(1, 6)]
    keyboard.add(*buttons)
    return keyboard
