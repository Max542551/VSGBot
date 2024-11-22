from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.get_to_db import get_order_by_id, get_taxi, get_sent_item_by_order
from handlers.taxi_handlers import main_menu_taxi
from keyboards.inline.orders_inline.user_order_inline.rating import get_rating_keyboard, get_user_rating_keyboard
from loader import dp, bot
from states.order_states import OrderStatus


def get_end_trip_button(order_id):
    markup = InlineKeyboardMarkup()
    end_trip_button = InlineKeyboardButton("🟢 Завершить поездку 🟢", callback_data=f"order_end_trip_{order_id}")
    markup.add(end_trip_button)
    return markup


@dp.callback_query_handler(lambda c: c.data.startswith('order_end_trip_'))
async def process_order_end_trip(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = int(callback_query.data.split("_")[3])
    order = get_order_by_id(order_id)
    taxi_id = callback_query.from_user.id
    taxi = await get_taxi(taxi_id)

    if order is None:
        await bot.send_message(callback_query.from_user.id, "Не удалось найти заказ.")
        return

    if order.status == OrderStatus.CANCELED:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⛔️ Заказ был отменен."
        )
        return

    order.status = OrderStatus.COMPLETED
    order.save()

    taxi.is_busy = False
    taxi.daily_order_count += 1
    taxi.daily_earnings += order.cost
    taxi.daily_order_sum += order.cost
    taxi.save()

    sent_item = get_sent_item_by_order(order)

    try:
        # Удалить сообщение
        await bot.delete_message(chat_id=taxi_id, message_id=sent_item.text_message_id)
    except Exception as e:
        print(f"⚠️ Ошибка при завершении заказа {e}")

    await main_menu_taxi.main_menu_taxi(callback_query.message)


    await bot.send_message(
        chat_id=order.user_id,
        text="✅ Ваша поездка завершена!\n\n\n"
             "🤗 Благодарим за использование нашего сервиса!\n"
             "Надеемся, что вам понравилось 😍\n\n"
             "🌠 Оцените пожалуйста вашу поездку",
        reply_markup=get_rating_keyboard(order.id)
    )

    await bot.send_message(
        chat_id=taxi.user_id,
        text="✅ Поездка завершена!\n\n\n"
             "🌠 Пожалуйста, оцените пассажира",
        reply_markup=get_user_rating_keyboard(order.user_id, order_id)
    )

    if sent_item:
        sent_item.delete_instance()

    await state.finish()
