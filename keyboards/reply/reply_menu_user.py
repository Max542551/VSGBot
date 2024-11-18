from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.default_handlers import start
from handlers.user_handlers import main_menu_user
from loader import dp


def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton('🏠 Главное меню')
    )


@dp.message_handler(lambda message: message.text == '🏠 Главное меню')
async def main_menu(message: types.Message, state: FSMContext):
    await state.reset_state()
    await start.start(message, state)
