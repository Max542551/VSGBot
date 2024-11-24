from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.get_to_db import delivery_get_sent_item_by_order, get_delivery_by_id, get_order_by_id, get_taxi, get_sent_item_by_order
from handlers.taxi_handlers import main_menu_taxi
from keyboards.inline.delivery_inline.delivery_raiting import delivery_get_rating_keyboard, delivery_rate_user_keyboard
from keyboards.inline.orders_inline.user_order_inline.rating import get_rating_keyboard, get_user_rating_keyboard
from loader import dp, bot
from states.delivery_states import DeliveryStatus
from states.order_states import OrderStatus


def get_end_delivery_button(order_id):
    markup = InlineKeyboardMarkup()
    end_trip_button = InlineKeyboardButton("🟢 Завершить доставку 🟢", callback_data=f"end_delivery_{order_id}")
    markup.add(end_trip_button)
    return markup


@dp.callback_query_handler(lambda c: c.data.startswith('end_delivery'))
async def process_end_delivery(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = int(callback_query.data.split("_")[-1])
    delivery = get_delivery_by_id(order_id)
    taxi_id = callback_query.from_user.id
    taxi = await get_taxi(taxi_id)

    if delivery is None:
        await bot.send_message(callback_query.from_user.id, "Не удалось найти заказ.")
        return

    if delivery.status == DeliveryStatus.CANCELED:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⛔️ Заказ был отменен."
        )
        return

    delivery.status = DeliveryStatus.COMPLETED
    delivery.save()

    taxi.is_busy = False
    taxi.daily_order_count += 1
    taxi.daily_earnings += delivery.cost
    taxi.daily_order_sum += delivery.cost
    taxi.save()

    sent_item = delivery_get_sent_item_by_order(delivery)

    try:
        # Удалить сообщение
        await bot.delete_message(chat_id=taxi_id, message_id=sent_item.text_message_id)
    except Exception as e:
        print(f"⚠️ Ошибка при завершении заказа {e}")

    await main_menu_taxi.main_menu_taxi(callback_query.message)


    await bot.send_message(
        chat_id=delivery.user_id,
        text="✅ Ваша доставка завершена!\n\n\n"
             "🤗 Благодарим за использование нашего сервиса!\n"
             "Надеемся, что вам понравилось 😍\n\n"
             "🌠 Оцените пожалуйста вашу доставку",
        reply_markup=delivery_get_rating_keyboard(delivery.id)
    )

    await bot.send_message(
        chat_id=taxi.user_id,
        text="✅ Доставка завершена!\n\n\n"
             "🌠 Пожалуйста, оцените заказчика",
        reply_markup=delivery_rate_user_keyboard(delivery.user_id, order_id)
    )

    if sent_item:
        sent_item.delete_instance()

    await state.finish()
