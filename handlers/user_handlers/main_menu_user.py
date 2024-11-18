from aiogram.types import InlineKeyboardMarkup
from database.get_to_db import get_user, has_orders, get_taxi, get_active_orders_by_user_id, get_free_taxis_count, \
 get_deferred_orders_user
from aiogram import types
from keyboards.inline.orders_inline.user_order_inline.cancel_order import determine_cancel_button
from keyboards.inline.user_inline.markup_main import markup_main
from utils.order_detail import calculate_order_details


async def main_menu(message: types.Message):
    user_id = message.chat.id
    user = await get_user(user_id)
    free_taxis_count = get_free_taxis_count()

    if has_orders(user_id):
        # Если есть заказы, выводим информацию о заказе
        # Получаем информацию о заказах пользователя
        orders = await get_active_orders_by_user_id(user_id)
        for order in orders:
            taxi = await get_taxi(order.taxi_id)
            cancel_order = await determine_cancel_button(order)
            cost = "Ждет предложения" if order.cost is None else f"{order.cost} руб"
            # Выводим информацию о каждом заказе
            await message.answer(f"📄 Информация о заказе №{order.id}:\n\n\n"
                                 f"👥️ <b>Количество пассажиров:</b> {order.count_passanger}\n\n"
                                 f"🚖 <b>Марка автомобиля:</b> {taxi.car if taxi else 'в поиске'}\n\n"
                                 f"🎨 <b>Цвет автомобиля:</b> {taxi.color_car if taxi else 'в поиске'}\n\n"
                                 f"🎰 <b>Гос. Номер:</b> {taxi.registration_number if taxi else 'в поиске'}\n\n\n"
                                 f"👨 <b>Имя водителя:</b> {taxi.name if taxi else 'в поиске'}\n\n"
                                 f"📈 <b>Рейтинг водителя:</b> {taxi.rating if taxi else 'в поиске'}\n\n"
                                 f"📱 <b>Телефон водителя:</b> {'+'+taxi.phone if taxi else 'в поиске'}\n\n\n"
                                 f"🟢 <b>Откуда едем:</b> {order.first_address}\n\n"
                                 f"🔴 <b>Куда едем:</b> {order.second_address}\n\n"
                                 f"👶 <b>Детское кресло:</b> {order.child_seat}\n\n"
                                 f"💰 <b>Стоимость:</b> {cost}\n\n"
                                 f"💵 <b>Оплата:</b> {order.payment_method}\n\n"
                                 f"💭 Комментарий к заказу: <b>{order.comment}</b>", reply_markup=cancel_order, parse_mode='html')
    else:
        if not user.is_active:
            await message.answer('❌️ Ваша учетная запись была деактивирована администратором.')
            return
        # Если нет заказов, выводим приветственное сообщение
        rating = round(user.rating, 2) if user.rating else "У вас еще нет оценок"
        await message.answer(f"👋 Привет, {user.name}!\n\n"
                             f"Пусть сегодня у вас все получится ❤️\n\n"
                             f"📈 <b>Ваш рейтинг:</b> {rating}\n\n"
                             f"Сейчас свободных машин: {free_taxis_count}", parse_mode='html',
                             reply_markup=markup_main())
        deferred_orders_buttons = get_deferred_orders_user(user_id)
        if deferred_orders_buttons:
            # Отправляем список отложенных заказов
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(*deferred_orders_buttons)
            await message.answer("❗ Отложенные заказы:", reply_markup=markup)
