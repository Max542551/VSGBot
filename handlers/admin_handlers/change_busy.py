from aiogram import types
from aiogram.dispatcher import FSMContext

from database.get_to_db import get_taxi
from loader import bot, dp
from states.admin_states import ChangeBusy

@dp.callback_query_handler(lambda c: c.data == "busy_off", state="*")
async def process_busy_off(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.send_message(callback_query.from_user.id, "Введите айди таксиста, у которого хотите снять статус is_busy")
    await ChangeBusy.GET_USER_ID.set()
    await callback_query.answer()

@dp.message_handler(state=ChangeBusy.GET_USER_ID)
async def process_change_busy(message: types.Message, state: FSMContext):
    user_id = message.text
    taxi = await get_taxi(user_id)
    if taxi:
        taxi.is_busy = False
        taxi.save()
        await bot.send_message(message.from_user.id, f"✅ Статус is_busy успешно снят у таксиста")
        await state.finish()
    else:
        await bot.send_message(message.from_user.id, f"⚠️ Пользователь не найден в базе данных!")
        await state.finish()