from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database.add_to_db import add_user
from database.get_to_db import get_taxi
from handlers.user_handlers import main_menu_user
from keyboards.reply import reply_menu_user
from loader import dp
from states.user_states import UserRegistrationState


@dp.message_handler(state=UserRegistrationState.name)
async def process_name_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await UserRegistrationState.next()

    # создаем клавиатуру
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    # добавляем кнопку для отправки контактных данных
    kb.add(KeyboardButton('📩 Отправить контактные данные', request_contact=True))

    await message.answer('📲 Пожалуйста, поделитесь своим контактом\n\n'
                         'Для этого нажмите кнопку <b>📩 Отправить контактные данные 📩</b>\n'
                         '🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽', reply_markup=kb, parse_mode='html')


@dp.message_handler(state=UserRegistrationState.phone, content_types=types.ContentType.CONTACT)
async def process_phone_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_name = data['name']
        # получаем номер телефона из контактных данных пользователя
        user_phone = message.contact.phone_number
        user_id = message.from_user.id

    taxi = await get_taxi(user_id)

    if taxi:
        taxi.is_active = False  # деактивируем таксиста
        taxi.save()

    add_user(user_id, user_name, user_phone)
    await message.answer('✅ Добро пожаловать на борт!',reply_markup=reply_menu_user.get_main_menu_keyboard())
    await main_menu_user.main_menu(message)
    await state.finish()