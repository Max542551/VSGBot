from aiogram import types
from aiogram.dispatcher import FSMContext

from database.get_to_db import get_taxi
from handlers.taxi_handlers import main_menu_taxi
from loader import bot, dp


@dp.callback_query_handler(lambda c: c.data == 'reset_daily_order_sum')
async def process_reset_daily_order_sum(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    taxi = await get_taxi(user_id)

    taxi.daily_order_sum = 0.0
    taxi.save()


    await bot.send_message(user_id, "✅ Сумма заказов за текущий день успешно сброшена.")
    await main_menu_taxi.main_menu_taxi(callback_query.message)
    await bot.answer_callback_query(callback_query.id)
