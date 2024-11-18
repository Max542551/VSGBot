from aiogram import types
from database.get_to_db import get_taxi
from handlers.taxi_handlers import main_menu_taxi
from loader import bot, dp
from states.taxi_states import TaxiRegistrationState


@dp.callback_query_handler(lambda c: c.data == 'switch_to_taxi')
async def process_callback_switch_to_taxi(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    taxi = await get_taxi(user_id)

    if taxi:
        if not taxi.admin_deactivated:
            taxi.is_active = True  # активируем таксиста
            taxi.save()

            await bot.edit_message_text('🔀 Вы сменили роль на водителя такси. Добро пожаловать!',
                                        chat_id=callback_query.from_user.id,
                                        message_id=callback_query.message.message_id)
            await main_menu_taxi.main_menu_taxi(callback_query.message)  # передаем callback_query вместо message
        else:
            await bot.edit_message_text('🚫 Ваш аккаунт водителя деактивирован администратором.',
                                        chat_id=callback_query.from_user.id,
                                        message_id=callback_query.message.message_id)
    else:
        await bot.edit_message_text(
            "🚖 Мы рады, что вы решили стать частью нашей команды! 🎉\n\n"
            "💳 Пожалуйста внесите единовременный регистрационный взнос 300 руб.\n"
            "Номер карты: <b>2202 2022 2910 6392 (Сбер)</b>\n\n"
            "📲 Отправьте скриншот перевода, на котором видны дата и время, как фотографию после этого сообщения:", chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id, parse_mode='html')
        await TaxiRegistrationState.waiting_for_payment_screenshot.set()
