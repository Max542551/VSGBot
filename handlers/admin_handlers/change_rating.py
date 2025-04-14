from aiogram import types
from aiogram.dispatcher import FSMContext

from database.database import Taxi, User
from database.get_to_db import get_taxi_by_phone, get_user_by_phone
from loader import bot, dp
from states.admin_states import ChangeRating

@dp.callback_query_handler(lambda c: c.data == 'change_rating', state="*")
async def process_user_id(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, f"Введите номер телефона пользователя")
    await state.set_state(ChangeRating.GET_USER_ID)
    await callback_query.answer()

@dp.message_handler(state=ChangeRating.GET_USER_ID)
async def process_change_rating(message: types.Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)
    taxi = get_taxi_by_phone(phone)
    user = get_user_by_phone(phone)
    if taxi:
        await bot.send_message(message.from_user.id, f"Введите новый рейтинг для таксиста")
        await state.set_state(ChangeRating.CHANGE_TAXI_RATING)
    elif user:
        await bot.send_message(message.from_user.id, f"Введите новый рейтинг для пользователя")
        await state.set_state(ChangeRating.CHANGE_USER_RATING)
    else:
        await bot.send_message(message.from_user.id, f"⚠️ Пользователь не найден в базе данных!")
        await state.finish()

@dp.message_handler(state=ChangeRating.CHANGE_TAXI_RATING)
async def process_change_taxi_rating(message: types.Message, state: FSMContext):
    new_rating = message.text
    data = await state.get_data()
    taxi = Taxi.get(Taxi.phone == data.get("phone"))
    taxi.rating = new_rating
    taxi.save()
    await bot.send_message(message.from_user.id, f"✅ Рейтинг успешно изменен на <b>{new_rating}</b>", parse_mode='html')
    await state.finish()

@dp.message_handler(state=ChangeRating.CHANGE_USER_RATING)
async def process_change_user_rating(message: types.Message, state: FSMContext):
    new_rating = message.text
    data = await state.get_data()
    user = User.get(User.phone == data.get("phone"))
    user.rating = new_rating
    user.save()
    await bot.send_message(message.from_user.id, f"✅ Рейтинг успешно изменен на <b>{new_rating}</b>", parse_mode='html')
    await state.finish()