from aiogram import types
from aiogram.dispatcher import FSMContext

from database.get_to_db import get_taxi
from handlers.taxi_handlers import main_menu_taxi
from loader import bot, dp


@dp.callback_query_handler(lambda call: call.data == 'towatch', state="*")
async def toggle_watch_mode(call: types.CallbackQuery, state: FSMContext):
    taxi_id = call.from_user.id
    taxi = await get_taxi(taxi_id)

    if taxi is None:
        await bot.send_message(call.message.chat.id, "⚠️ Таксист не найден.")
        return

    if taxi.shift:
        await bot.answer_callback_query(call.id, show_alert=True,
                                        text="⚠️ Для начала наблюдения, завершите смену!\n\n")
        return

    # Переключаем режим наблюдения
    taxi.is_watching = not taxi.is_watching
    taxi.save()

    # Отправляем сообщение пользователю о статусе наблюдения
    watch_status = "активировано" if taxi.is_watching else "деактивировано"
    await bot.edit_message_text(chat_id=call.from_user.id,
                           message_id=call.message.message_id, text=f"👁️ Режим наблюдения {watch_status}.")
    await main_menu_taxi.main_menu_taxi(call.message)
    await bot.answer_callback_query(call.id)
