from aiogram import types
from aiogram.dispatcher import FSMContext
from handlers.taxi_handlers import main_menu_taxi
from loader import dp


def taxi_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('🏡 Главное меню'))
    return keyboard


@dp.message_handler(lambda message: message.text == '🏡 Главное меню')
async def handle_main_menu(message: types.Message, state: FSMContext):
    await state.reset_state()
    await main_menu_taxi.main_menu_taxi(message)
