from aiogram import types
from aiogram.dispatcher import FSMContext

from database.database import Taxi, User
from database.get_to_db import get_taxi_by_phone, get_user_by_phone
from loader import bot, dp
from states.admin_states import ChangePhone

@dp.callback_query_handler(lambda c: c.data == 'change_phone', state="*")
async def process_change_phone(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.send_message(callback_query.from_user.id, "Введите номер телефона пользователя, который хотите изменить")
    await ChangePhone.GET_PHONE.set()
    await callback_query.answer()

@dp.message_handler(state=ChangePhone.GET_PHONE)
async def process_user_id(message: types.Message, state: FSMContext):
    old_phone = message.text
    taxi = get_taxi_by_phone(old_phone)
    user = get_user_by_phone(old_phone)
    if taxi:
        await bot.send_message(message.from_user.id, f"Введите новый номер телефона для таксиста")
        await state.set_state(ChangePhone.CHANGE_TAXI_PHONE)
        await state.update_data(taxi_id=taxi.user_id)
    elif user:
        await bot.send_message(message.from_user.id, f"Введите новый номер телефона для пользователя")
        await state.set_state(ChangePhone.CHANGE_USER_PHONE)
        await state.update_data(user_id=user.user_id)
    # if taxi:
    #     await bot.send_message(message.from_user.id, f"✅ Номер телефона успешно изменен на <b>{new_phone}</b>",
    #                            parse_mode='html')
    else:
        await bot.send_message(message.from_user.id, f"⚠️ Номер телефона не найден в базе данных!")
        await state.finish()

@dp.message_handler(state=ChangePhone.CHANGE_TAXI_PHONE)
async def process_change_taxi_phone(message: types.Message, state: FSMContext):
    new_phone = message.text
    data = await state.get_data()
    taxi = Taxi.get(Taxi.user_id == data.get("taxi_id"))
    taxi.phone = new_phone
    taxi.save()
    await bot.send_message(message.from_user.id, f"✅ Номер телефона успешно изменен на <b>{new_phone}</b>",
                           parse_mode='html')
    await state.finish()

@dp.message_handler(state=ChangePhone.CHANGE_USER_PHONE)
async def process_change_user_phone(message: types.Message, state: FSMContext):
    new_phone = message.text
    data = await state.get_data()
    user = User.get(User.user_id == data.get("user_id"))
    user.phone = new_phone
    user.save()
    await bot.send_message(message.from_user.id, f"✅ Номер телефона успешно изменен на <b>{new_phone}</b>",
                           parse_mode='html')
    await state.finish()