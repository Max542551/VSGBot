from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.get_to_db import get_user
from database.update_to_db import update_user_address
from loader import dp, bot
from states.user_states import UserAddressChange


@dp.callback_query_handler(lambda c: c.data == 'my_addresses')
async def my_addresses(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user = await get_user(user_id)
    home_address = user.home_address if user.home_address else "Не указан"
    work_address = user.work_address if user.work_address else "Не указан"

    reply_markup = InlineKeyboardMarkup(row_width=1)
    reply_markup.add(
        InlineKeyboardButton("➕ Добавить/Изменить адрес Дом", callback_data='add_home'),
        InlineKeyboardButton("➕ Добавить/Изменить адрес Работа", callback_data='add_work')
    )

    await bot.send_message(callback_query.from_user.id,
                           "👇Ваши текущие адреса:\n\n"
                           f"🏠 Дом: {home_address}\n"
                           f"💼 Работа: {work_address}",
                           reply_markup=reply_markup)


@dp.callback_query_handler(lambda c: c.data == 'add_home', state="*")
async def prompt_home_address(callback_query: types.CallbackQuery):
    await UserAddressChange.waiting_for_home_address.set()
    await bot.send_message(callback_query.from_user.id, "✍️ Введите ваш домашний адрес:")

@dp.message_handler(state=UserAddressChange.waiting_for_home_address)
async def update_home_address(message: types.Message, state: FSMContext):
    home_address = message.text
    user_id = message.from_user.id
    update_user_address(user_id, home_address=home_address)
    await message.answer("✅ Ваш домашний адрес обновлен.")
    await state.reset_state()


@dp.callback_query_handler(lambda c: c.data == 'add_work', state="*")
async def prompt_work_address(callback_query: types.CallbackQuery):
    await UserAddressChange.waiting_for_work_address.set()  # Переводим пользователя в состояние ожидания ввода рабочего адреса
    await bot.send_message(callback_query.from_user.id, "✍️ Введите ваш рабочий адрес:")


@dp.message_handler(state=UserAddressChange.waiting_for_work_address)
async def update_work_address(message: types.Message, state: FSMContext):
    work_address = message.text
    user_id = message.from_user.id
    update_user_address(user_id, work_address=work_address)  # Обновляем рабочий адрес пользователя в базе данных
    await message.answer("✅ Ваш рабочий адрес обновлен.")
    await state.reset_state()  # Сбрасываем состояние пользователя
