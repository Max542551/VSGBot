from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.get_to_db import get_delivery_by_id
from keyboards.inline.delivery_inline.delivery_status_buttons.leaving_with_package import get_leaving_with_package_button
from loader import dp, bot
from states.delivery_states import DeliveryStatus


def get_delivery_package_button(order_id):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("🟡 Я получаю посылку 🟡", callback_data=f"delivery_get_package_{order_id}")
    )


@dp.callback_query_handler(lambda c: c.data.startswith('delivery_get_package'), state="*")
async def process_delivery_expectation(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = int(callback_query.data.split("_")[-1])
    taxi_id = callback_query.from_user.id
    # print("tyt")
    delivery = get_delivery_by_id(order_id)
    if delivery is None:
        await bot.send_message(taxi_id, "Не удалось найти заказ.")
        return

    if delivery.taxi_id != taxi_id:
        await bot.send_message(taxi_id, "Этот заказ не принадлежит вам.")
        return

    if delivery.status == DeliveryStatus.CANCELED or delivery.status == DeliveryStatus.COMPLETED:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⛔️ Заказ был отменен."
        )
        return

    delivery.status = DeliveryStatus.GET_PACKAGE
    delivery.save()


    await bot.edit_message_reply_markup(
        chat_id=taxi_id,
        message_id=callback_query.message.message_id,
        reply_markup=get_leaving_with_package_button(order_id)
    )

    await bot.send_message(
        chat_id=delivery.user_id,
        text=f"Доставщик получил посылку"
    )

    await bot.answer_callback_query(callback_query.id)
    await state.finish()
