import json

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config_data.config import group_id
from database.get_to_db import get_delivery_by_id
from keyboards.inline.delivery_inline.delivery_status_buttons.in_place import in_place_button
from loader import bot, dp
from states.delivery_states import DeliveryStatus


def get_leaving_with_package_button(order_id):
    markup = InlineKeyboardMarkup()
    leaving_button = InlineKeyboardButton("Выехал с посылкой", callback_data=f"leaving_with_package_{order_id}")
    markup.add(leaving_button)
    return markup


@dp.callback_query_handler(lambda c: c.data.startswith('leaving_with_package'))
async def process_start_trip(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = int(callback_query.data.split("_")[-1])
    taxi_id = callback_query.from_user.id

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

    delivery.status = DeliveryStatus.LEAVING
    delivery.save()


    await bot.edit_message_reply_markup(
        chat_id=taxi_id,
        message_id=callback_query.message.message_id,
        reply_markup=in_place_button(order_id)
    )

    await bot.send_message(
        chat_id=delivery.user_id,
        text=f"Доставщик выехал с посылкой"
    )

    await bot.answer_callback_query(callback_query.id)
    await state.finish()
