from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.get_to_db import get_order_by_id
from keyboards.inline.orders_inline.taxi_order_inline.start_trip import get_start_trip_button
from loader import dp, bot
from states.order_states import OrderStatus


def get_expectation_button(order_id):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("🟡 Я приехал 🟡", callback_data=f"order_expectation_{order_id}")
    )


@dp.callback_query_handler(lambda c: c.data.startswith('order_expectation_'))
async def process_order_expectation(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = int(callback_query.data.split("_")[2])
    taxi_id = callback_query.from_user.id

    order = get_order_by_id(order_id)
    if order is None:
        await bot.send_message(taxi_id, "Не удалось найти заказ.")
        return

    if order.taxi_id != taxi_id:
        await bot.send_message(taxi_id, "Этот заказ не принадлежит вам.")
        return

    if order.status == OrderStatus.CANCELED or order.status == OrderStatus.COMPLETED:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⛔️ Заказ был отменен."
        )
        return

    order.status = OrderStatus.EXPECTATION
    order.save()


    await bot.edit_message_reply_markup(
        chat_id=taxi_id,
        message_id=callback_query.message.message_id,
        reply_markup=get_start_trip_button(order_id)
    )

    await bot.send_message(
        chat_id=order.user_id,
        text=f"🚕 Ваш автомобиль прибыл и ожидает вас."
    )

    await bot.answer_callback_query(callback_query.id)
    await state.finish()
