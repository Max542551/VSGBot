from typing import List, Tuple
from aiogram import types

from loader import dp, bot


def create_address_keyboard(locations: List[Tuple[str, float, float]]) -> types.InlineKeyboardMarkup:
    buttons = [
        types.InlineKeyboardButton(
            text=addr, callback_data=f"location:{lat}:{lon}"
        )
        for addr, lat, lon in locations
    ]

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)

    return keyboard


@dp.callback_query_handler(lambda c: c.data.startswith('address:'))
async def process_callback_address(callback_query: types.CallbackQuery):
    _, address_index = callback_query.data.split(':')
    address_index = int(address_index)

    await bot.answer_callback_query(callback_query.id)