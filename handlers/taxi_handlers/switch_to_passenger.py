from aiogram import types
from aiogram.dispatcher.filters import state

from database.get_to_db import get_taxi, get_user
from handlers.user_handlers import main_menu_user
from loader import bot, dp
from states.user_states import UserRegistrationState


@dp.callback_query_handler(lambda c: c.data == 'switch_to_passenger')
async def process_callback_switch_to_passenger(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    taxi = await get_taxi(user_id)

    user = await get_user(user_id)  # проверяем, зарегистрирован ли пользователь как пассажир
    if user:
        if taxi:
            taxi.is_active = False  # деактивируем таксиста
            taxi.save()

        # если да, переходим в главное меню пассажиров
        await bot.edit_message_text('🔀 Вы сменили роль на пассажир. Добро пожаловать!',
                                    chat_id=callback_query.from_user.id,
                                    message_id=callback_query.message.message_id)
        await main_menu_user.main_menu(callback_query.message)

    else:
        # если нет, начинаем процесс регистрации пассажира
        await bot.edit_message_text('🙋‍♂️Вам нужно пройти регистрацию пассажира!\n\n'
                                    '🔆 Введите ваше имя:', chat_id=callback_query.from_user.id,
                                    message_id=callback_query.message.message_id)
        await UserRegistrationState.name.set()
