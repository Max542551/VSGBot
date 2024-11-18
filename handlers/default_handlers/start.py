from aiogram import types
from aiogram.dispatcher import FSMContext

from database.get_to_db import get_user, get_taxi
from handlers.taxi_handlers import main_menu_taxi
from handlers.user_handlers import main_menu_user
from keyboards.inline.welcome import generate_welcome_keyboard
from loader import dp, bot
from states.taxi_states import TaxiRegistrationState
from states.user_states import UserRegistrationState


@dp.message_handler(commands=["start"], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    user = await get_user(user_id)  # Используйте await здесь
    taxi = await get_taxi(user_id)

    if user and taxi is not None:
        if not taxi.is_active:
            await main_menu_user.main_menu(message)
        else:
            await main_menu_taxi.main_menu_taxi(message)
    elif user:
        await main_menu_user.main_menu(message)
    elif taxi:
        await main_menu_taxi.main_menu_taxi(message)
    else:
        welcome_message = "🎉 Добро пожаловать в <b>Такси Бота</b>! 🎉\n\n" \
                          "🚀 Мы рады, что вы выбрали нас для своих поездок.\n\n" \
                          "🙃 В каком статусе вы присоединяетесь к нам?\n\n" \

        await message.reply(welcome_message, reply_markup=generate_welcome_keyboard(), reply=False, parse_mode='html')


@dp.callback_query_handler(lambda c: c.data == 'passenger')
async def process_callback_passenger(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text('🔆 Введите ваше имя:', chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id)
    await UserRegistrationState.name.set()


@dp.callback_query_handler(lambda c: c.data == 'taxi')
async def process_callback_taxi(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "💳 Пожалуйста внесите единовременный регистрационный взнос 300 руб.\n"
        "Номер карты: <b>2202 2022 2910 6392 (Сбер)</b>\n\n"
        "📲 Отправьте скриншот перевода, на котором видны дата и время, как фотографию после этого сообщения:",
        parse_mode='html'
    )
    await TaxiRegistrationState.waiting_for_payment_screenshot.set()