import time
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types

from database.add_to_db import create_delivery_in_db
from database.get_to_db import get_delivery_by_user_id, get_free_deliveries_count
from keyboards.inline.delivery_inline.cancel_buttons import delivery_cancel_order_buttons
from keyboards.inline.orders_inline.user_order_inline.cancel_order import cancel_order_buttons
from loader import dp, bot

from states.delivery_states import DeliveryState
from handlers.default_handlers.start import start
from keyboards.inline.orders_inline.user_order_inline.payment_method import payment_keyboard
from keyboards.inline.orders_inline.user_order_inline.cost import cost_keyboard
from keyboards.inline.orders_inline.user_order_inline.comment import comment_keyboard
from keyboards.reply.reply_menu_user import get_main_menu_keyboard
from utils import message_for_deliveryman

@dp.callback_query_handler(lambda call: call.data == 'user_delivery_order', state="*")
async def order_request(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(user_id=call.from_user.id)

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.insert(InlineKeyboardButton("✅ Заказать доставку", callback_data="delivery_confirm"))
    keyboard.insert(InlineKeyboardButton("❌ Отменить", callback_data="delivery_cancel"))

    count_deliveries = get_free_deliveries_count()
    message_text = f"<b>ВАШ ЗАКАЗ ПОЛУЧАТ {count_deliveries} ВОДИТЕЛЕЙ</b>\n\n" \

    await call.message.answer(
        f"<b>ВАШ ЗАКАЗ ПОЛУЧАТ {count_deliveries} ВОДИТЕЛЕЙ</b>\n\n⚠️ Вы создаете доставку на определенную дату и время. После принятия вашего заказа, обязательно свяжитесь с водителем по телефону и убедитесь в его готовности выполнения заказа. Администрация приложения не несёт ответственности за выполнение заказов. Ответственными за выполнение заказа являетесь только Вы как пассажир и водитель.",
        reply_markup=keyboard, parse_mode='html')
    
@dp.callback_query_handler(lambda call: call.data == 'delivery_confirm', state="*")
async def confirm_order(call: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="📍 Откуда доставить, и во сколько?\n\n🔅 <b>Введите адрес доставки и время (г.Меленки ул. Мира д.1 подъезд 2   01.01.2024 в 10.30):</b>",
                                parse_mode='html')
    await DeliveryState.FIRST_LOCATION.set()


@dp.callback_query_handler(lambda call: call.data == 'delivery_cancel', state="*")
async def cancel_order(call: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id, text="❌ Вы отказались от создания доставки.")
    
@dp.message_handler(state=DeliveryState.FIRST_LOCATION)
async def handle_first_location(message: types.Message, state: FSMContext):
    if message.text.startswith('🏠 Главное меню'):
        await start(message, state)
        return

    state_data = await state.get_data()
    state_data["first_address"] = message.text
    await state.set_data(state_data)

    await bot.send_message(message.chat.id,
                           "⛳️ Куда доставить?",
                           parse_mode='html')

    await DeliveryState.SECOND_LOCATION.set()

# @dp.message_handler(state=DeliveryState.SECOND_LOCATION)
# async def handle_second_location(message: types.Message, state: FSMContext):
#     if message.text.startswith('🏠 Главное меню'):
#         await start(message, state)
#         return

#     state_data = await state.get_data()
#     state_data["second_address"] = message.text
#     await state.set_data(state_data)
#     await bot.send_message(message.chat.id, "🗓 Когда и во сколько доставить?")
#     await DeliveryState.DELIVERY_DATE.set()

@dp.message_handler(state=DeliveryState.SECOND_LOCATION)
async def handle_second_location(message: types.Message, state: FSMContext):
    if message.text.startswith('🏠 Главное меню'):
        await start(message, state)
        return

    state_data = await state.get_data()
    state_data["second_address"] = message.text
    await state.set_data(state_data)
    await bot.send_message(message.chat.id, "📦 Что в посылке?")
    await DeliveryState.PACKAGE_CONTENT.set()

@dp.message_handler(state=DeliveryState.PACKAGE_CONTENT)
async def handle_cost(message: types.Message, state: FSMContext):
    if message.text.startswith('🏠 Главное меню'):
        await start(message, state)
        return

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.insert(InlineKeyboardButton("✅ Посылка оплачена", callback_data="delivery_paid"))
    keyboard.insert(InlineKeyboardButton("Посылку необходимо оплатить", callback_data="delivery_unpaid"))

    state_data = await state.get_data()
    state_data["package_content"] = message.text
    await state.set_data(state_data)
    await bot.send_message(message.chat.id, "Оплата посылки", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data == 'delivery_paid', state="*")
async def paid_delivery(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    state_data["package_payment"] = "Клиент оплатил"
    await state.set_data(state_data)

    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="Способ олпаты",
                                parse_mode='html',
                                reply_markup=payment_keyboard())
    await DeliveryState.PAYMENT_METHOD.set()

@dp.callback_query_handler(lambda call: call.data == 'delivery_unpaid', state="*")
async def unpaid_delivery(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    state_data["package_payment"] = "Нужно оплатить водителю"
    await state.set_data(state_data)

    await bot.edit_message_text(chat_id=call.message.chat.id,
                                message_id=call.message.message_id, text="Сколько нужно заплатить?")
    await DeliveryState.HOW_MUCH_PAY.set()

@dp.message_handler(state=DeliveryState.HOW_MUCH_PAY)
async def handle_amount_pay(message: types.CallbackQuery, state: FSMContext):
    if message.text.startswith('🏠 Главное меню'):
        await start(message, state)
        return

    state_data = await state.get_data()
    state_data["package_price"] = message.text
    await state.set_data(state_data)
    await bot.send_message(message.chat.id, "Способ олпаты", reply_markup=payment_keyboard())
    await DeliveryState.PAYMENT_METHOD.set()

@dp.callback_query_handler(state=DeliveryState.PAYMENT_METHOD, text=["Наличные", "Перевод"])
async def handle_payment(call: types.CallbackQuery, state: FSMContext):
    if call.message.text.startswith('🏠 Главное меню'):
        await start(call.message, state)
        return

    state_data = await state.get_data()
    state_data["payment_method"] = call.data
    state_data["cost"] = None
    await state.set_data(state_data)

    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(call.message.chat.id,
                            "✍️ Желаете оставить комментарий к заказу? :",
                            reply_markup=comment_keyboard())
    await DeliveryState.COMMENT.set()

# @dp.callback_query_handler(state=DeliveryState.COST, text=["specify_amount", "request_offers"])
# async def handle_cost(call: types.CallbackQuery, state: FSMContext):
#     if call.message.text.startswith('🏠 Главное меню'):
#         await start(call.message, state)
#         return

#     state_data = await state.get_data()
#     if call.data == "specify_amount":
#         await bot.edit_message_text("💰 Введите желаемую сумму доставки (только цифры!):",
#                                     chat_id=call.message.chat.id,
#                                     message_id=call.message.message_id)
#         await DeliveryState.SPECIFY_AMOUNT.set()
#     else:
#         state_data["cost"] = None
#         await state.set_data(state_data)

#         await bot.delete_message(call.message.chat.id, call.message.message_id)
#         await bot.send_message(call.message.chat.id,
#                                 "✍️ Желаете оставить комментарий к заказу? :",
#                                 reply_markup=comment_keyboard())
#         await DeliveryState.COMMENT.set()

# @dp.message_handler(state=DeliveryState.SPECIFY_AMOUNT, content_types=['text'])
# async def handle_specify_amount(message: types.Message, state: FSMContext):
#     if message.text.startswith('🏠 Главное меню'):
#         await start(message, state)
#         return

#     state_data = await state.get_data()
#     try:
#         amount = int(message.text)
#         state_data["cost"] = amount
#         await state.set_data(state_data)

#         await bot.send_message(message.chat.id,
#                                 "✍️ Желаете оставить комментарий к заказу? :",
#                                 reply_markup=comment_keyboard())

#         await DeliveryState.COMMENT.set()
#     except ValueError:
#         await bot.send_message(message.chat.id, "⚠️ Введите корректную сумму.")


@dp.message_handler(state=DeliveryState.COMMENT)
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
    create_delivery_in_db(state_data)
    user_id = message.chat.id
    order = get_delivery_by_user_id(user_id)
    cancel_order = delivery_cancel_order_buttons(order.id)

    if order: 
        message_text = f"⚠️После принятия вашего заказа, обязательно свяжитесь с водителем по телефону и убедитесь в его готовности выполнения заказа.\n\n" \
            f"Администрация приложения не несёт ответственности за выполнение заказов.\n\n" \
            f"Ответственными за выполнение заказа являетесь только Вы как заказчик и водитель."
        await bot.send_message(message.chat.id, message_text,
                               reply_markup=get_main_menu_keyboard(), parse_mode="html")
        time.sleep(2)
        await message.answer("👀 Ищу для вас подходящего заказчика ", reply_markup=cancel_order)

        await message_for_deliveryman.notify_delivery_drivers(order, first_address, second_address)

        await state.finish()  # завершаем сценарий и очищаем данные состояния
    else:
        await bot.send_message(message.chat.id,
                               "⚠️ Произошла ошибка при сохранении заказа. Пожалуйста, начните заказ заново.",
                               reply_markup=get_main_menu_keyboard())