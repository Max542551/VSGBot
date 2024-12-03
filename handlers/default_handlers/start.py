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
        welcome_message = "🎉 Добро пожаловать в <b>Такси Бота 'VSG' г.Меленки</b>! 🎉\n\n" \
                          "🚀 Му уверены что Вы оцените удобство и преимущества бота. \n\n" \
                        "Бот не является таксопарком и агрегатором такси, а информационный портал. \n\n" \
                        "Создан для удобства жителей города и района \n\n" \
                        "Объединяет все такси города в одном удобном формате. \n\n" \
                          "🙃 В каком статусе вы присоединяетесь к боту?\n\n" \

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
        "🚖 Мы рады, что вы решили стать частью нашей команды! 🎉\n\n"
            "💳 Пожалуйста внесите единовременный регистрационный взнос 300 руб.\n"
            "Номер карты: <b>2200 7009 8038 6675 (Тинькофф банк Алексей Витальевич У.)</b>\n\n"
            "📲 Отправьте скриншот перевода, на котором видны дата и время, как фотографию после этого сообщения:",
        parse_mode='html'
    )
    await TaxiRegistrationState.waiting_for_payment_screenshot.set()