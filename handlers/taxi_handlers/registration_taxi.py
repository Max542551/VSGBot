import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config_data.config import ADMIN_IDS
from database.add_to_db import add_taxi
from handlers.admin_handlers.decision_buttons import make_registration_decision_buttons
from handlers.taxi_handlers import main_menu_taxi
from keyboards.inline.taxi_inline.child_seat import reg_child_seat_keyboard
from keyboards.reply.reply_menu_user import get_main_menu_keyboard
from states.taxi_states import TaxiRegistrationState
from loader import bot, dp


@dp.message_handler(content_types=['photo'], state=TaxiRegistrationState.waiting_for_payment_screenshot)
async def receive_registration_payment_screenshot(message: types.Message, state: FSMContext):
    for admin_id in ADMIN_IDS:
        await bot.forward_message(admin_id, message.chat.id, message.message_id)
        decision_buttons = make_registration_decision_buttons(message.from_user.id)
        await bot.send_message(admin_id,
                               f"❗ Получен скриншот платежа от {message.from_user.full_name} за регистрацию.",
                               reply_markup=decision_buttons)

    await bot.send_message(message.chat.id,
                           "✅ Спасибо, ваш платеж отправлен на проверку администратору. После подтверждения вы получите уведомление!")


@dp.callback_query_handler(lambda c: c.data.startswith('reg_accept') or c.data.startswith('jer_regtaxi'))
async def process_admin_registration_decision(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split(":")[1])

    if callback_query.data.startswith("reg_accept"):
        await bot.edit_message_text('✅ Принято', callback_query.message.chat.id,
                                    callback_query.message.message_id)
        await bot.send_message(user_id, "✅ Ваша оплата подтверждена. Давайте начнем процесс регистрации.")

        # Задаем состояние для пользователя, а не для администратора
        state = dp.current_state(chat=user_id, user=user_id)
        await state.set_state(TaxiRegistrationState.name)
        await bot.send_message(user_id, '🔆 Введите ваше имя:')
    elif callback_query.data.startswith("jer_regtaxi"):
        await bot.edit_message_text('❌ Отклонено', callback_query.message.chat.id,
                                    callback_query.message.message_id)
        await bot.send_message(user_id, "❌ Ваша регистрация отклонена.")


@dp.message_handler(state=TaxiRegistrationState.name)
async def process_name_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await TaxiRegistrationState.phone.set()
    # создаем клавиатуру
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    # добавляем кнопку для отправки контактных данных
    kb.add(KeyboardButton('📩 Отправить контактные данные 📩', request_contact=True))

    await message.answer('📲 Пожалуйста, поделитесь своим контактом\n\n'
                         'Для этого нажмите кнопку <b>📩 Отправить контактные данные 📩</b>\n'
                         '🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽🔽', reply_markup=kb, parse_mode='html')


@dp.message_handler(state=TaxiRegistrationState.phone, content_types=types.ContentType.CONTACT)
async def process_phone_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.contact.phone_number
    await TaxiRegistrationState.next()
    await message.answer('🚖 Введите марку вашего автомобиля\n'
                         '(в формате: Киа Рио):')


@dp.message_handler(state=TaxiRegistrationState.car)
async def process_car_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['car'] = message.text
    await TaxiRegistrationState.next()
    await message.answer('🎨 Введите цвет вашего автомобиля\n'
                         '(в формате: Белый):')


@dp.message_handler(state=TaxiRegistrationState.color_car)
async def process_color_car_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['color_car'] = message.text
    await TaxiRegistrationState.next()
    await message.answer('🎰 Введите регистрационный номер вашего автомобиля\n'
                         '(в формате: А 777 АА 77):')


@dp.message_handler(state=TaxiRegistrationState.registration_number)
async def process_registration_number_step(message: types.Message, state: FSMContext):
    registration_number = message.text.upper()
    if not re.match(r'^[А-ЯA-Z]{1} \d{3} [А-ЯA-Z]{2} \d{2,3}$', registration_number):
        await message.reply("Неверный формат номера. Пожалуйста, введите номер в формате: А 777 АА 77 или А 777 АА 777")
        return
    async with state.proxy() as data:
        data['registration_number'] = registration_number
    await TaxiRegistrationState.next()
    await message.answer('👶 У вас есть детские кресла?', reply_markup=reg_child_seat_keyboard())


@dp.callback_query_handler(lambda c: c.data in ['child_seat_yes', 'child_seat_no'],
                           state=TaxiRegistrationState.child_seat)
async def process_child_seat_step(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['child_seat'] = callback_query.data == 'child_seat_yes'
        user_id = callback_query.from_user.id
        add_taxi(user_id, data['name'], data['phone'], data['car'], data['color_car'], data['registration_number'],
                 data['child_seat'])
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, '✅ К штурвалу, капитан!',
                           reply_markup=get_main_menu_keyboard())
    await main_menu_taxi.main_menu_taxi(callback_query.message)
    await state.finish()
