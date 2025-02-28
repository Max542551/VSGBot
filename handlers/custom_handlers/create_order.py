import time
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.add_to_db import create_order_in_db
from database.get_to_db import get_order_by_user_id, get_user
from handlers.default_handlers.start import start
from keyboards.inline.orders_inline.pass_keyboard import passengers_keyboard
from keyboards.inline.orders_inline.user_order_inline.cancel_order import cancel_order_buttons
from keyboards.inline.orders_inline.user_order_inline.child_seat import child_seat_keyboard
from keyboards.inline.orders_inline.user_order_inline.comment import comment_keyboard
from keyboards.inline.orders_inline.user_order_inline.cost import cost_keyboard
from keyboards.inline.orders_inline.user_order_inline.payment_method import payment_keyboard
from keyboards.reply.reply_menu_user import get_main_menu_keyboard
from loader import dp, bot
from states.order_states import TaxiOrderState
from utils import message_for_taxi

from config_data.config import min_price


@dp.callback_query_handler(lambda call: call.data == 'userdef_order', state="*")
async def deferred_order_request(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(user_id=call.from_user.id, deferred=True)

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.insert(InlineKeyboardButton("✅ Сделать предзаказ", callback_data="condefer"))
    keyboard.insert(InlineKeyboardButton("❌ Отменить", callback_data="cadefer"))

    await call.message.answer(
        "⚠️ Вы создаёте предзаказ такси на определённую дату и время. После принятия вашего заказа, обязательно свяжитесь с водителем по телефону и убедитесь в его готовности выполнения заказа. Администрация приложения не несёт ответственности за выполнение заказов. Ответственными за выполнение заказа являетесь только Вы как пассажир и водитель. \n\n"
        "<b> По вопросам грузовых и грузопассажирский перевозок обращаться по тел. +79051472649</b>", 
        reply_markup=keyboard, parse_mode='html')


@dp.callback_query_handler(lambda call: call.data == 'condefer', state="*")
async def confirm_deferred_order(call: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="📍 Откуда Вас забрать позже, и во сколько?\n\n🔅 <b>Введите адрес отправления и время (г.Меленки ул. Мира д.1 подъезд 2   01.01.2025 в 10.30):</b>",
                                parse_mode='html')
    await TaxiOrderState.FIRST_LOCATION.set()


@dp.callback_query_handler(lambda call: call.data == 'cadefer', state="*")
async def cancel_deferred_order(call: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id, text="❌ Вы отказались от создания предзаказа.")
    await state.finish()


@dp.callback_query_handler(lambda call: call.data == 'order_a_taxi', state="*")
async def location_request(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    user = await get_user(user_id)

    if call.message.text.startswith('🏠 Главное меню'):
        await start(call.message, state)
        return

    if not user.is_active:
        await call.message.answer('❌️ Ваша учетная запись была деактивирована администратором.')
        return

    quick_address_keyboard = InlineKeyboardMarkup(row_width=2)
    quick_address_keyboard.insert(InlineKeyboardButton("🏠 Из дома", callback_data="home_address"))
    quick_address_keyboard.insert(InlineKeyboardButton("💼 С работы", callback_data="work_address"))

    await state.update_data(user_id=call.from_user.id, deferred=False)
    await call.message.answer("📍 Откуда Вас забрать?\n\n"
                              "🔅 <b>Введите адрес (с указанием № подъезда):</b>", reply_markup=quick_address_keyboard,
                              parse_mode='html')
    await TaxiOrderState.FIRST_LOCATION.set()


@dp.callback_query_handler(lambda call: call.data in ["home_address", "work_address"],
                           state=TaxiOrderState.FIRST_LOCATION)
async def set_quick_first_location(call: types.CallbackQuery, state: FSMContext):
    user = await get_user(call.from_user.id)
    # Определяем, какой адрес выбран и проверяем его наличие
    chosen_address = "home_address" if call.data == "home_address" else "work_address"
    address_to_use = user.home_address if chosen_address == "home_address" else user.work_address

    # Если выбранный адрес отсутствует
    if not address_to_use:
        await bot.answer_callback_query(call.id, show_alert=True,
                                        text=f"⚠️ У вас нету сохраненного адреса {'дома' if chosen_address == 'home_address' else 'работы'}, добавьте его в главном меню!")
        return

    address = user.home_address if call.data == "home_address" else user.work_address
    state_data = await state.get_data()
    state_data["first_address"] = address
    await state.set_data(state_data)

    quick_address_keyboard = InlineKeyboardMarkup(row_width=2)
    quick_address_keyboard.insert(InlineKeyboardButton("🏠 Домой", callback_data="second_home_address"))
    quick_address_keyboard.insert(InlineKeyboardButton("💼 На работу", callback_data="second_work_address"))

    # Переход к запросу второго адреса
    await TaxiOrderState.SECOND_LOCATION.set()
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id, text=f"✅ Выбран адрес: {address}\n\n"
                                                                         "⛳️ Куда едем?\n\n"
                                                                         "🔅 <b>Введите адрес (с указанием № подъезда):</b>",
                                reply_markup=quick_address_keyboard, parse_mode='html')  # Убираем предыдущую клавиатуру


@dp.message_handler(state=TaxiOrderState.FIRST_LOCATION)
async def handle_first_location(message: types.Message, state: FSMContext):
    if message.text.startswith('🏠 Главное меню'):
        await start(message, state)
        return

    state_data = await state.get_data()
    state_data["first_address"] = message.text
    await state.set_data(state_data)

    quick_address_keyboard = InlineKeyboardMarkup(row_width=2)
    quick_address_keyboard.insert(InlineKeyboardButton("🏠 Домой", callback_data="second_home_address"))
    quick_address_keyboard.insert(InlineKeyboardButton("💼 На работу", callback_data="second_work_address"))

    await bot.send_message(message.chat.id,
                           "⛳️ Куда едем?\n\n"
                           "🔅 <b>Введите адрес (с указанием № подъезда):</b>", reply_markup=quick_address_keyboard,
                           parse_mode='html')

    await TaxiOrderState.SECOND_LOCATION.set()


@dp.callback_query_handler(lambda call: call.data in ["second_home_address", "second_work_address"],
                           state=TaxiOrderState.SECOND_LOCATION)
async def set_quick_second_location(call: types.CallbackQuery, state: FSMContext):
    user = await get_user(call.from_user.id)
    # Определяем, какой адрес выбран и проверяем его наличие
    chosen_address = "second_home_address" if call.data == "second_home_address" else "second_work_address"
    address_to_use = user.home_address if chosen_address == "second_home_address" else user.work_address

    # Если выбранный адрес отсутствует
    if not address_to_use:
        await bot.answer_callback_query(call.id, show_alert=True,
                                        text=f"⚠️ У вас нету сохраненного адреса {'дома' if chosen_address == 'second_home_address' else 'работы'}, добавьте его в главном меню!")
        return

    address = user.home_address if call.data == "second_home_address" else user.work_address

    state_data = await state.get_data()
    state_data["second_address"] = address
    await state.set_data(state_data)
    # После установки адреса переходим к выбору детского кресла
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id, text=f"✅ Выбран адрес: {address}\n\n"
                                                                         "👶 Вам требуются детское кресло?",
                                reply_markup=child_seat_keyboard())
    await TaxiOrderState.BABY_SEAT.set()


@dp.message_handler(state=TaxiOrderState.SECOND_LOCATION)
async def handle_second_location(message: types.Message, state: FSMContext):
    if message.text.startswith('🏠 Главное меню'):
        await start(message, state)
        return

    state_data = await state.get_data()
    state_data["second_address"] = message.text
    await state.set_data(state_data)
    await bot.send_message(message.chat.id, "👶 Вам требуются детское кресло?", reply_markup=child_seat_keyboard())
    await TaxiOrderState.BABY_SEAT.set()


@dp.callback_query_handler(state=TaxiOrderState.BABY_SEAT, text=["Нужно", "Не нужно"])
async def handle_baby_seat(call: types.CallbackQuery, state: FSMContext):
    if call.message.text.startswith('🏠 Главное меню'):
        await start(call.message, state)
        return

    state_data = await state.get_data()
    state_data["child_seat"] = call.data
    await state.set_data(state_data)
    await bot.edit_message_text("👥 Укажите количество пассажиров:",
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                reply_markup=await passengers_keyboard())
    await TaxiOrderState.PASSENGERS.set()


@dp.callback_query_handler(state=TaxiOrderState.PASSENGERS, text_startswith="passenger_")
async def handle_passengers(call: types.CallbackQuery, state: FSMContext):
    passengers_count = int(call.data.split('_')[1])
    await state.update_data(count_passanger=passengers_count)

    await bot.edit_message_text("💸 Выберите способ оплаты", chat_id=call.message.chat.id,
                                message_id=call.message.message_id, reply_markup=payment_keyboard())

    await TaxiOrderState.PAYMENT_METHOD.set()


@dp.callback_query_handler(state=TaxiOrderState.PAYMENT_METHOD, text=["Наличные", "Перевод"])
async def handle_payment(call: types.CallbackQuery, state: FSMContext):
    if call.message.text.startswith('🏠 Главное меню'):
        await start(call.message, state)
        return

    state_data = await state.get_data()
    state_data["payment_method"] = call.data
    await state.set_data(state_data)

    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(call.message.chat.id, "💰 Какая цена Вас интересует?",
                           reply_markup=cost_keyboard())
    await TaxiOrderState.COST.set()


@dp.callback_query_handler(state=TaxiOrderState.COST, text=["specify_amount", "request_offers"])
async def handle_cost(call: types.CallbackQuery, state: FSMContext):
    if call.message.text.startswith('🏠 Главное меню'):
        await start(call.message, state)
        return

    state_data = await state.get_data()
    if call.data == "specify_amount":
        await bot.edit_message_text("💰 Введите желаемую сумму поездки (только цифры!):",
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id)
        await TaxiOrderState.SPECIFY_AMOUNT.set()
    else:
        state_data["cost"] = None
        await state.set_data(state_data)

        await bot.delete_message(call.message.chat.id, call.message.message_id)
        if state_data["deferred"]:
            await bot.send_message(call.message.chat.id,
                                   "✍️ Оставьте комментарий к заказу, максимально подробно опишите детали поездки обязательно укажите дату и время отправления:")
        else:
            await bot.send_message(call.message.chat.id,
                                   "✍️ Желаете оставить комментарий к заказу? :",
                                   reply_markup=comment_keyboard())
        await TaxiOrderState.COMMENT.set()


@dp.message_handler(state=TaxiOrderState.SPECIFY_AMOUNT, content_types=['text'])
async def handle_specify_amount(message: types.Message, state: FSMContext):
    if message.text.startswith('🏠 Главное меню'):
        await start(message, state)
        return
    state_data = await state.get_data()
    try:
        if int(message.text) < min_price:
            await bot.send_message(message.chat.id, f"Минимальная стоимость поездки по городу {min_price} руб. Пожалуйста введите сумму равную или больше минимальной")
            return
        amount = int(message.text)
        state_data["cost"] = amount
        await state.set_data(state_data)

        if state_data["deferred"]:
            await bot.send_message(message.chat.id,
                                   "✍️ Оставьте комментарий к заказу, максимально подробно опишите детали поездки обязательно укажите дату и время отправления:")
        else:
            await bot.send_message(message.chat.id,
                                   "✍️ Желаете оставить комментарий к заказу? :",
                                   reply_markup=comment_keyboard())

        await TaxiOrderState.COMMENT.set()
    except ValueError:
        await bot.send_message(message.chat.id, "⚠️ Введите корректную сумму.")


@dp.message_handler(state=TaxiOrderState.COMMENT)
async def handle_comment(message: types.Message, state: FSMContext):
    if message.text.startswith('🏠 Главное меню'):
        await start(message, state)
        return

    state_data = await state.get_data()
    state_data["comment"] = message.text if message.text != "⛔️ Без комментариев" else "-"
    first_address = state_data["first_address"]
    second_address = state_data["second_address"]

    await state.set_data(state_data)
    # создаем заказ в базе данных и получаем его
    create_order_in_db(state_data)
    user_id = message.chat.id
    order = get_order_by_user_id(user_id)
    cancel_order = cancel_order_buttons(order.id)

    if order:
        await bot.send_message(message.chat.id, "👍 Заказ создан!\n\n"
                                                "Когда водитель примет заказ, мы вас оповестим!",
                               reply_markup=get_main_menu_keyboard())
        time.sleep(2)
        await message.answer("👀 Ищу для вас подходящий автомобиль ", reply_markup=cancel_order)

        if order.deferred:
            # вызываем функцию для оповещения водителей
            await message_for_taxi.notify_taxi_drivers_deffer(order, first_address, second_address)
        else:
            # вызываем функцию для оповещения водителей
            await message_for_taxi.notify_taxi_drivers(order, first_address, second_address)

        await state.finish()  # завершаем сценарий и очищаем данные состояния
    else:
        await bot.send_message(message.chat.id,
                               "⚠️ Произошла ошибка при сохранении заказа. Пожалуйста, начните заказ заново.",
                               reply_markup=get_main_menu_keyboard())
