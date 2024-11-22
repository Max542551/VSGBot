from aiogram import types
from aiogram.dispatcher import FSMContext

from database.get_to_db import get_taxi
from handlers.taxi_handlers import main_menu_taxi
from loader import bot, dp


@dp.callback_query_handler(lambda call: call.data == 'deliveryon', state="*")
async def toggle_delivery_mode(call: types.CallbackQuery, state: FSMContext):
    taxi_id = call.from_user.id
    taxi = await get_taxi(taxi_id)

    if taxi is None:
        await bot.send_message(call.message.chat.id, "⚠️ Таксист не найден.")
        return

    # Переключаем режим наблюдения
    taxi.delivery_active = not taxi.delivery_active
    taxi.save()

    # Отправляем сообщение пользователю о статусе наблюдения
    delivery_status = "Активирован режим доставки" if taxi.delivery_active else "Деактивирован режим доставки"
    await bot.edit_message_text(chat_id=call.from_user.id,
                           message_id=call.message.message_id, text=f"{delivery_status}.")
    await main_menu_taxi.main_menu_taxi(call.message)
    await bot.answer_callback_query(call.id)
