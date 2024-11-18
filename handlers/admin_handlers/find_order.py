from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from peewee import DoesNotExist

from database.database import Order
from database.get_to_db import get_user, get_taxi, get_order_by_id
from keyboards.inline.orders_inline.user_order_inline.cancel_order import cancel_order_buttons
from keyboards.inline.orders_inline.user_order_inline.rating import get_rating_keyboard, get_user_rating_keyboard
from loader import dp, bot
from states.admin_states import AdminFindOrder
from states.order_states import OrderStatus


def order_management_buttons(order_id):
    markup = InlineKeyboardMarkup(row_width=1)
    start_trip_button = InlineKeyboardButton("🚦 Начать поездку", callback_data=f"start_trip_{order_id}")
    complete_trip_button = InlineKeyboardButton("✅ Завершить поездку", callback_data=f"complete_trip_{order_id}")
    cancel_order_button = InlineKeyboardButton("❌ Отменить заказ", callback_data=f"cancel_order_{order_id}")

    markup.add(start_trip_button, complete_trip_button, cancel_order_button)
    return markup


@dp.callback_query_handler(lambda c: c.data == 'find_order')
async def admin_find_order(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await AdminFindOrder.waiting_for_order_number.set()
    await bot.send_message(callback_query.from_user.id, "Введите номер заказа:")


@dp.message_handler(state=AdminFindOrder.waiting_for_order_number)
async def order_info(message: types.Message, state: FSMContext):
    order_id = message.text
    order = Order.get_or_none(Order.id == order_id)

    if order:
        user = await get_user(order.user_id)
        taxi = await get_taxi(order.taxi_id)
        order_info = f"❓ Информация о заказе №{order_id}:\n\n\n" \
                     f"👥️ <b>Количество пассажиров:</b> {order.count_passanger}\n\n" \
                     f"👥 <b>Имя пассажира:</b> {user.name}\n\n" \
                     f"📱 <b>Номер пассажира:</b> {user.phone}\n\n\n" \
                     f"👨 <b>Имя водителя:</b> {taxi.name if order.taxi_id else 'Не определен'}\n\n" \
                     f"🚖 <b>Цвет/Марка автомобиля:</b> {taxi.color_car if order.taxi_id else 'Не определен'} {taxi.car if order.taxi_id else 'Не определен'}\n\n" \
                     f"🎰 <b>Гос. Номер:</b> {taxi.registration_number if order.taxi_id else 'Не определен'}\n\n\n" \
                     f"📍 <b>Откуда:</b> {order.first_address}\n\n" \
                     f"📍 <b>Куда:</b> {order.second_address}\n\n" \
                     f"💰 <b>Стоимость: </b> {order.cost}\n\n" \
                     f"🚦 <b>Статус:</b> {order.status}\n\n" \
                     f"👶 <b>Детское кресло:</b> {order.child_seat}\n\n" \
                     f"💵 <b>Метод оплаты:</b> {order.payment_method}\n\n" \
                     f"💬 <b>Комментарий:</b> {order.comment}\n\n" \
                     f"⭐ <b>Рейтинг:</b> {order.rating}"
        await bot.send_message(message.from_user.id, order_info, parse_mode='html',
                               reply_markup=order_management_buttons(order_id))
    else:
        await bot.send_message(message.from_user.id, "🤷‍♂️ Заказа с таким номером не найдено.")

    await state.finish()  # завершаем сценарий


@dp.callback_query_handler(lambda c: c.data.startswith('start_trip_'))
async def start_trip(callback_query: types.CallbackQuery):
    order_id = callback_query.data.split('_')[-1]

    try:
        order = Order.get_by_id(order_id)
        order.status = OrderStatus.TRIP  # Обновляем статус
        order.save()

        await bot.send_message(order.user_id, "🚕💨 Ваша поездка началась! Приятного пути ❤️")
        await bot.send_message(order.taxi_id, "🚕💨 Администратор начал вашу поездку!\n\n"
                                              "Перейдите в главное меню для просмотра информации")

    except DoesNotExist:
        await bot.send_message(callback_query.from_user.id, "Заказ не найден.")


@dp.callback_query_handler(lambda c: c.data.startswith('complete_trip_'))
async def complete_trip(callback_query: types.CallbackQuery):
    order_id = callback_query.data.split('_')[-1]
    order = get_order_by_id(order_id)
    taxi = await get_taxi(order.taxi_id)

    try:
        order = Order.get_by_id(order_id)
        order.status = OrderStatus.COMPLETED  # Обновляем статус
        order.save()

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
            text="✅ Поездка завершена Администратором!\n\n\n"
                 "🌠 Пожалуйста, оцените пассажира",
            reply_markup=get_user_rating_keyboard(order.user_id)
        )

        taxi.is_busy = False
        taxi.daily_order_count += 1
        taxi.daily_earnings += order.cost
        taxi.save()


    except DoesNotExist:
        await bot.send_message(callback_query.from_user.id, "Заказ не найден.")
