from aiogram import types
from aiogram.dispatcher import FSMContext

from database.database import User
from database.get_to_db import get_passenger_by_phone
from loader import bot, dp
from states.admin_states import UserInfoState


def generate_passenger_keyboard():
    passengers = User.select()
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    for passenger in passengers:
        btn = types.InlineKeyboardButton(f'{passenger.name}', callback_data=f'infor_passenger_{passenger.user_id}')
        inline_kb.add(btn)
    return inline_kb


def generate_passenger_info_keyboard(passenger_id):
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    btn_deactivate = types.InlineKeyboardButton("🚷 Деактивировать/ активировать",
                                                callback_data=f'toggles_passenger_{passenger_id}')
    btn_change_name = types.InlineKeyboardButton("👤 Изменить имя",
                                                 callback_data=f'changes_name_passenger_{passenger_id}')
    inline_kb.add(btn_deactivate, btn_change_name)
    return inline_kb


def generate_passenger_info(passenger):
    passenger_status = "🟥" if not passenger.is_active else "🟩"
    link = f"<a href='tg://user?id={passenger.user_id}'>Написать в лс</a>"
    info_text = (f"👤 <b>Имя:</b> {passenger.name}\n\n"
                 f"📞 <b>Телефон:</b> {passenger.phone}\n\n"
                 f"⭐️ <b>Рейтинг:</b> {passenger.rating}\n\n"
                 f"{passenger_status} <b>Статус активации:</b> {'Активирован' if passenger.is_active else 'Деактивирован'}\n\n"
                 f"{link}")
    return info_text


@dp.callback_query_handler(lambda c: c.data == 'passtogle')
async def toggle_passenger_activation(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "📲 Пожалуйста, введите номер телефона пассажира:")
    await UserInfoState.REQUEST_PHONE.set()


@dp.message_handler(state=UserInfoState.REQUEST_PHONE, content_types=types.ContentTypes.TEXT)
async def passenger_by_phone(message: types.Message, state: FSMContext):
    phone_number = message.text
    # Здесь вам понадобится функция для получения пассажира по номеру телефона
    passenger = get_passenger_by_phone(phone_number)
    if passenger:
        inline_kb = generate_passenger_info_keyboard(passenger.user_id)
        info_text = generate_passenger_info(passenger)
        await bot.send_message(message.from_user.id, info_text, reply_markup=inline_kb, parse_mode='html')
    else:
        await bot.send_message(message.from_user.id, "🤷‍♂️ Пассажир с данным номером телефона не найден.")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('toggles_passenger_'))
async def process_passenger_toggle(callback_query: types.CallbackQuery):
    passenger_id = int(callback_query.data.split('_')[2])
    passenger = User.get(User.user_id == passenger_id)

    if not passenger.is_active:
        passenger.is_active = True
        await bot.send_message(callback_query.from_user.id, f'✅ Пассажир {passenger.name} активирован ✅')
        await bot.send_message(passenger.user_id, '🎉 Ваша учетная запись была активирована администратором.')
    else:
        passenger.is_active = False
        await bot.send_message(callback_query.from_user.id, f'❌ Пассажир {passenger.name} деактивирован ❌')
        await bot.send_message(passenger.user_id, '⚠️ Ваша учетная запись была деактивирована администратором.')

    passenger.save()

    # обновляем клавиатуру и текст с информацией о пассажире
    info_text = generate_passenger_info(passenger)
    keyboard = generate_passenger_info_keyboard(passenger_id)
    await bot.edit_message_text(text=info_text, chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id, parse_mode='html', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('changes_name_passenger_'), state='*')
async def prompt_passenger_name(callback_query: types.CallbackQuery, state: FSMContext):
    await UserInfoState.CHANGE_NAME.set()
    user_id = int(callback_query.data.split('_')[3])
    await state.update_data(user_id=user_id)
    await bot.send_message(callback_query.from_user.id, "Введите новое имя для пассажира:")


@dp.message_handler(state=UserInfoState.CHANGE_NAME, content_types=types.ContentTypes.TEXT)
async def update_passenger_name(message: types.Message, state: FSMContext):
    new_name = message.text
    async with state.proxy() as data:
        user_id = data['user_id']
    user = User.get(User.user_id == user_id)

    try:
        user.name = new_name
        user.save()
        await message.answer(f"✅ Имя пассажира успешно обновлено на: {new_name}")
    except User.DoesNotExist:
        await message.answer("Пассажира с таким ID не найдено!")
    finally:
        await state.finish()
