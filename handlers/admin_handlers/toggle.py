from aiogram import types
from aiogram.dispatcher import FSMContext

from database.database import Taxi
from database.get_to_db import get_taxi, get_taxi_by_phone
from loader import bot, dp
from states.admin_states import TaxiDriverInfoState


def generate_keyboard():
    taxis = Taxi.select()
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    for taxi in taxis:
        taxi_status = "🟥" if taxi.admin_deactivated else "🟩"
        btn = types.InlineKeyboardButton(f'{taxi_status} {taxi.name} | {taxi.registration_number}',
                                         callback_data=f'info_{taxi.user_id}')
        inline_kb.add(btn)
    return inline_kb


def generate_taxi_info_keyboard(taxi_id):
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_deactivate = types.InlineKeyboardButton("🚷 Деактивировать/ активировать", callback_data=f'toggle_{taxi_id}')
    btn_change_car = types.InlineKeyboardButton("🚖 Изменить марку автомобиля", callback_data=f'change_car_{taxi_id}')
    btn_change_color = types.InlineKeyboardButton("🎨 Изменить цвет автомобиля", callback_data=f'change_color_{taxi_id}')
    btn_change_number = types.InlineKeyboardButton("🎰 Изменить гос. номер", callback_data=f'change_number_{taxi_id}')
    btn_change_balance = types.InlineKeyboardButton("💰 Изменить баланс", callback_data=f'change_balance_{taxi_id}')
    btn_change_name = types.InlineKeyboardButton("👤 Изменить имя", callback_data=f'change_name_{taxi_id}')
    btn_end_shift = types.InlineKeyboardButton("🛑 Завершить смену", callback_data=f'end_shift_{taxi_id}')
    inline_kb.add(btn_deactivate, btn_change_car, btn_change_color, btn_change_number, btn_change_balance,
                  btn_change_name, btn_end_shift)
    return inline_kb


@dp.callback_query_handler(lambda c: c.data == 'toggle_driver')
async def request_phone_number(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "📲 Пожалуйста, введите номер телефона водителя:")
    await TaxiDriverInfoState.REQUEST_PHONE.set()


@dp.callback_query_handler(lambda c: c.data.startswith('toggle_'))
async def process_driver_toggle(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    taxi_id = int(callback_query.data.split('_')[1])
    taxi = Taxi.get(Taxi.user_id == taxi_id)
    if not taxi.admin_deactivated:
        taxi.admin_deactivated = True
        await bot.send_message(callback_query.from_user.id, f'❌ Водитель {taxi.name} деактивирован ❌')
        await bot.send_message(taxi.user_id, '⚠️ Ваша учетная запись была деактивирована администратором.')
    else:
        taxi.admin_deactivated = False
        await bot.send_message(callback_query.from_user.id, f'✅ Водитель {taxi.name} активирован ✅')
        await bot.send_message(taxi.user_id, '🎉 Ваша учетная запись была активирована администратором.')
    taxi.save()

    # generate a new keyboard and replace the old one
    new_keyboard = generate_taxi_info_keyboard(taxi_id)
    info_text = generate_taxi_info(taxi)
    await bot.edit_message_text(text=info_text, chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id, reply_markup=new_keyboard,
                                parse_mode='html')


def generate_taxi_info(taxi):
    taxi_status = "🟥" if taxi.admin_deactivated else "🟩"
    link = f"<a href='tg://user?id={taxi.user_id}'>Написать в лс</a>"
    info_text = (f"👤 <b>Имя:</b> {taxi.name}\n\n"
                 f"📞 <b>Телефон:</b> {taxi.phone}\n\n"
                 f"⭐️ <b>Рейтинг:</b> {taxi.rating}\n\n\n"
                 f"🚖 <b>Марка автомобиля:</b> {taxi.car}\n\n"
                 f"🎨 <b>Цвет автомобиля:</b> {taxi.color_car}\n\n"
                 f"🎰 <b>Гос. Номер:</b> {taxi.registration_number}\n\n"
                 f"{taxi_status} <b>Статус активации:</b> {'Активирован' if not taxi.admin_deactivated else 'Деактивирован'}\n\n"
                 f"{link}")
    return info_text


@dp.message_handler(state=TaxiDriverInfoState.REQUEST_PHONE, content_types=types.ContentTypes.TEXT)
async def get_driver_by_phone(message: types.Message, state: FSMContext):
    phone_number = message.text
    # Here you will need a function to fetch a taxi driver by phone number
    taxi = get_taxi_by_phone(phone_number)
    if taxi:
        inline_kb = generate_taxi_info_keyboard(taxi.user_id)
        info_text = generate_taxi_info(taxi)
        await bot.send_message(message.from_user.id, info_text, reply_markup=inline_kb, parse_mode='html')
    else:
        await bot.send_message(message.from_user.id, "🤷‍♂️ Водитель с данным номером телефона не найден.")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('change_car_'))
async def process_change_car(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    taxi_id = int(callback_query.data.split('_')[2])
    await state.update_data(taxi_id=taxi_id)
    await bot.edit_message_text(text="🚖 Введите новую марку автомобиля:", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    await TaxiDriverInfoState.CHANGE_CAR.set()


@dp.message_handler(state=TaxiDriverInfoState.CHANGE_CAR)
async def handle_change_car(message: types.Message, state: FSMContext):
    new_car = message.text
    async with state.proxy() as data:
        taxi_id = data['taxi_id']
    taxi = Taxi.get(Taxi.user_id == taxi_id)
    taxi.car = new_car
    taxi.save()
    await bot.send_message(message.from_user.id, f"✅ Марка автомобиля успешно изменена на <b>{new_car}</b>",
                           parse_mode='html')
    await state.finish()


# аналогичные обработчики для изменения цвета и номера


@dp.callback_query_handler(lambda c: c.data.startswith('change_color_'))
async def process_change_color(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    taxi_id = int(callback_query.data.split('_')[2])
    await state.update_data(taxi_id=taxi_id)
    await bot.edit_message_text(text="🎨 Введите новый цвет автомобиля:", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    await TaxiDriverInfoState.CHANGE_COLOR.set()


@dp.message_handler(state=TaxiDriverInfoState.CHANGE_COLOR)
async def handle_change_color(message: types.Message, state: FSMContext):
    new_color = message.text
    async with state.proxy() as data:
        taxi_id = data['taxi_id']
    taxi = Taxi.get(Taxi.user_id == taxi_id)
    taxi.color_car = new_color
    taxi.save()
    await bot.send_message(message.from_user.id, f"✅ Цвет автомобиля успешно изменен на <b>{new_color}</b>",
                           parse_mode='html')
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('change_number_'))
async def process_change_number(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    taxi_id = int(callback_query.data.split('_')[2])
    await state.update_data(taxi_id=taxi_id)
    await bot.edit_message_text(text="🎰 Введите новый государственный номер:", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    await TaxiDriverInfoState.CHANGE_NUMBER.set()


@dp.message_handler(state=TaxiDriverInfoState.CHANGE_NUMBER)
async def handle_change_number(message: types.Message, state: FSMContext):
    new_number = message.text.upper()
    async with state.proxy() as data:
        taxi_id = data['taxi_id']
    taxi = Taxi.get(Taxi.user_id == taxi_id)
    taxi.registration_number = new_number
    taxi.save()
    await bot.send_message(message.from_user.id, f"✅ Государственный номер успешно изменен на <b>{new_number}</b>",
                           parse_mode='html')
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('change_balance_'))
async def process_change_balance(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    taxi_id = int(callback_query.data.split('_')[2])
    taxi = await get_taxi(taxi_id)
    await state.update_data(taxi_id=taxi_id)
    await bot.edit_message_text(text=f"Текущий баланс водителя: {taxi.balance}\n\n"
                                     "💰 Введите новый баланс:", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    await TaxiDriverInfoState.CHANGE_BALANCE.set()


@dp.message_handler(state=TaxiDriverInfoState.CHANGE_BALANCE)
async def handle_change_balance(message: types.Message, state: FSMContext):
    new_balance = message.text
    async with state.proxy() as data:
        taxi_id = data['taxi_id']
    taxi = Taxi.get(Taxi.user_id == taxi_id)
    taxi.balance = new_balance  # Предполагая, что у вас есть поле 'balance' в модели Taxi
    taxi.save()
    await bot.send_message(message.from_user.id, f"✅ Баланс успешно изменен на <b>{new_balance}</b> руб",
                           parse_mode='html')
    await bot.send_message(taxi_id, f"💰 Ваш баланс изменен на <b>{new_balance}</b> руб", parse_mode='html')
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('change_name_'), state='*')
async def prompt_taxi_name(callback_query: types.CallbackQuery, state: FSMContext):
    await TaxiDriverInfoState.CHANGE_NAME.set()
    taxi_id = int(callback_query.data.split('_')[2])
    await state.update_data(taxi_id=taxi_id)
    await bot.send_message(callback_query.from_user.id, "Введите новое имя для таксиста:")


@dp.message_handler(state=TaxiDriverInfoState.CHANGE_NAME, content_types=types.ContentTypes.TEXT)
async def update_taxi_name(message: types.Message, state: FSMContext):
    new_name = message.text
    async with state.proxy() as data:
        taxi_id = data['taxi_id']
    taxi = Taxi.get(Taxi.user_id == taxi_id)

    try:
        taxi.name = new_name
        taxi.save()
        await message.answer(f"✅ Имя таксиста успешно обновлено на: {new_name}")
    except Taxi.DoesNotExist:
        await message.answer("Таксиста с таким ID не найдено!")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('end_shift_'))
async def process_end_shift(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    taxi_id = int(callback_query.data.split('_')[2])
    taxi = Taxi.get(Taxi.user_id == taxi_id)

    if taxi.shift:
        taxi.shift = False
        taxi.save()
        await bot.send_message(callback_query.from_user.id, f'✅ Смена для {taxi.name} завершена ✅')
        await bot.send_message(taxi.user_id, '🛑 Ваша смена была завершена администратором.')
    else:
        await bot.send_message(callback_query.from_user.id, f'❗️ Смена для {taxi.name} уже завершена ❗️')

