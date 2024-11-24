import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext

from config_data import config
from database.get_to_db import get_all_unique_users, get_all_drivers, get_all_passengers, get_all_passengers_null
from loader import dp, bot
from states.admin_states import AdminState


@dp.callback_query_handler(lambda c: c.data == 'admin_broadcast_all')
async def admin_broadcast_all(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(user_id=call.from_user.id, broadcast_type="all")
    await call.message.answer("✍️ Введите сообщение для общей рассылки")
    await AdminState.BROADCAST.set()


@dp.callback_query_handler(lambda c: c.data == 'admin_broadcast_drivers')
async def admin_broadcast_drivers(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(user_id=call.from_user.id, broadcast_type="drivers")
    await call.message.answer("✍️ Введите сообщение для рассылки водителям")
    await AdminState.BROADCAST.set()


@dp.callback_query_handler(lambda c: c.data == 'admin_broadcast_passengers')
async def admin_broadcast_passengers(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(user_id=call.from_user.id, broadcast_type="passengers")
    await call.message.answer("✍️ Введите сообщение для рассылки пассажирам")
    await AdminState.BROADCAST.set()


@dp.callback_query_handler(lambda c: c.data == 'nullpassengers')
async def admin_broadcast_passengers_null(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(user_id=call.from_user.id, broadcast_type="null")
    await call.message.answer("✍️ Введите сообщение для рассылки пассажирам null")
    await AdminState.BROADCAST.set()

@dp.message_handler(state=AdminState.BROADCAST)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    if message.text.startswith('/'):
        return
    broadcast_message = message.text
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type")

    if broadcast_type == "all":
        users = get_all_unique_users()
    elif broadcast_type == "drivers":
        users = get_all_drivers()
    elif broadcast_type == "passengers":
        users = get_all_passengers()
    elif broadcast_type == "null":
        users = get_all_passengers_null()
    else:
        users = []

    admin_id = int(config.ADMIN_ID)
    for user_id in users:
        if user_id != admin_id:  # пропускаем админа
            try:
                await bot.send_message(user_id, broadcast_message)
                await message.answer(f"✅ Сообщения отправлено {user_id}")
                await asyncio.sleep(15)  # отправляем сообщение каждому пользователю
            except Exception as e:
                print(f'Ошибка: {e}')
                pass

    await state.finish()  # завершаем сценарий
    await message.answer("✅ Сообщения отправлены")
