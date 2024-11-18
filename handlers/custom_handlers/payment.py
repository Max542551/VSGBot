from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery

from config_data.config import ADMIN_IDS
from database.get_to_db import get_taxi
from handlers.admin_handlers.decision_buttons import make_decision_buttons
from loader import bot, dp
from states.taxi_states import TaxiState


@dp.callback_query_handler(text='top_up')
async def top_up(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text("💸 Введите сумму для пополнения:", callback_query.message.chat.id,
                                callback_query.message.message_id)
    await TaxiState.waiting_for_top_up_amount.set()


@dp.message_handler(state=TaxiState.waiting_for_top_up_amount)
async def receive_top_up_amount(message: types.Message, state: FSMContext):
    amount = message.text
    if amount.isdigit() and int(amount) > 0:
        await state.update_data(amount=int(amount))
        await bot.send_message(message.from_user.id,
                               "💳 <b>2202 2022 2910 6392 (Сбер)</b>\n\n"
                               "Пополните на карту сумму, которую указали ранее\n\n"
                               "📲 Теперь отправьте скриншот перевода, на котором видны дата и время, как фотографию после этого сообщения:",
                               parse_mode='html')
        await TaxiState.waiting_for_payment_screenshot.set()
    else:
        await bot.send_message(message.from_user.id, "Введите корректную сумму!")


@dp.message_handler(content_types=['photo'], state=TaxiState.waiting_for_payment_screenshot)
async def receive_payment_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get('amount')

    for admin_id in ADMIN_IDS:
        await bot.forward_message(admin_id, message.chat.id, message.message_id)

        # Use the function to create decision buttons
        decision_buttons = make_decision_buttons(message.from_user.id, amount)
        await bot.send_message(admin_id,
                               f"❗ Получен скриншот платежа на {amount} руб от {message.from_user.full_name}.",
                               reply_markup=decision_buttons)

    await bot.send_message(message.chat.id,
                           "✅ Спасибо, ваш платеж отправлен на проверку администратору. После подтверждения вы получите уведомление!")
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('accept') or c.data.startswith('reject'))
async def process_admin_decision(callback_query: CallbackQuery, state: FSMContext):
    action, user_id, amount = callback_query.data.split(":")
    user_id = int(user_id)
    amount = int(amount)
    taxi = await get_taxi(user_id)


    if action == "accept":
        taxi.balance += amount
        taxi.save()
        await bot.edit_message_text('✅ Принято', callback_query.message.chat.id,
                                    callback_query.message.message_id)
        await bot.send_message(user_id, f"✅ Ваш платеж был одобрен. На ваш баланс зачислено: {amount} руб")
    else:
        await bot.edit_message_text('❌ Отклонено', callback_query.message.chat.id, callback_query.message.message_id)
        await bot.send_message(user_id,
                               "❌ Ваш платеж был отклонен. Пожалуйста, если у вас остались вопросы, свяжитесь с поддержкой.")

    await state.finish()
