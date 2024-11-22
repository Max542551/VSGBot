from aiogram import types

from database.get_to_db import get_order_by_id, get_taxi
from keyboards.inline.orders_inline.user_order_inline.cancel_order import cancel_order_buttons
from loader import dp, bot
from states.order_states import OrderStatus
from utils.order_detail import calculate_order_details


@dp.callback_query_handler(lambda c: 'user_deferred_orders' in c.data)
async def process_deferred_order_for_user(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    order_id = int(callback_query.data.split('_')[3])
    order = get_order_by_id(order_id)
    if order.status == OrderStatus.CANCELED or order.status == OrderStatus.COMPLETED:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Заказ был уже выполнен, либо отменен\n\n")
        return

    taxi = await get_taxi(order.deferred_by)
    cost = "Ждет предложения" if order.cost is None else f"{order.cost} руб"
    message_text = f"❗️<b>Отложенный заказ</b>\n\n\n" \
                   f"🚖 <b>Марка автомобиля:</b> {taxi.car}\n\n" \
                   f"🎨 <b>Цвет автомобиля:</b> {taxi.color_car}\n\n" \
                   f"🎰 <b>Гос. Номер:</b> {taxi.registration_number}\n\n\n" \
                   f"👨 <b>Имя водителя:</b> {taxi.name}\n\n" \
                   f"📈 <b>Рейтинг водителя:</b> {taxi.rating}\n\n" \
                   f"📱 <b>Телефон водителя:</b> {taxi.phone}\n\n\n" \
                   f"🅰️ <b>Откуда едем:</b> {order.first_address}\n\n" \
                   f"🅱️ <b>Куда едем:</b> {order.second_address}\n\n" \
                   f"💰 <b>Стоимость:</b> {cost}\n\n." \
                   f"💵 <b>Оплата:</b> {order.payment_method}\n\n" \
                   f"👶 <b>Детское кресло:</b> {order.child_seat}\n\n\n" \
                   f"💭 Комментарий к заказу: <b>{order.comment}</b>"

    await bot.send_message(callback_query.from_user.id, text=message_text, reply_markup=cancel_order_buttons(order_id),
                           parse_mode='html')
