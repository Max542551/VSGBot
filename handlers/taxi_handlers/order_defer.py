from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.add_to_db import save_sent_messages
from database.get_to_db import get_order_by_id, get_sent_messages, get_taxi, get_user
from keyboards.inline.taxi_inline.reply_accept_the_order import order_acceptance_keyboard_without_propose_price, \
    order_acceptance_keyboard
from loader import dp, bot
from states.order_states import OrderStatus


@dp.callback_query_handler(lambda c: 'order_defer' in c.data)
async def process_order_defer(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    order_id = int(callback_query.data.split('_')[2])
    taxi_id = callback_query.from_user.id
    taxi = await get_taxi(taxi_id)
    order = get_order_by_id(order_id)

    if order.deferred_by:
        await bot.edit_message_text(text="⛔️ Заказ уже принят другим водителем",
                                    chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id)
        return

    order.deferred_by = taxi_id
    order.status = OrderStatus.DEFERRED
    order.save()
    await bot.edit_message_text(text="✅ Заказ отложен\n\n"
                                     "Перейдите в 🏡 Главное меню для просмотра информации",
                                chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    await bot.send_message(order.user_id,
                           f"✅ Водитель <b>{taxi.name}</b> принял ваш заказ и выполнит в назначенное время!\n\n"
                           f"Перейдите в 🏠 Главное меню для просмотра информации об отложенном заказе",
                           parse_mode='html')

    # Удалить сообщения у всех таксистов, кроме того, который отложил заказ
    sent_messages = get_sent_messages(order_id)
    for user_id, message_id in sent_messages:
        if user_id != taxi_id:
            await bot.delete_message(chat_id=user_id, message_id=message_id)

    # Обновить сохраненные сообщения, чтобы оставить только сообщение для таксиста, который отложил заказ
    try:
        save_sent_messages(order_id, [(taxi_id, message_id)])
    except UnboundLocalError:
        pass


@dp.callback_query_handler(lambda c: 'deferred_order' in c.data)
async def process_deferred_order(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    order_id = int(callback_query.data.split('_')[2])
    order = get_order_by_id(order_id)
    if order.status == OrderStatus.CANCELED or order.status == OrderStatus.COMPLETED:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Заказ был уже выполнен, либо отменен\n\n")
        return

    user = await get_user(order.user_id)

    cost = order.cost

    message_text = f"❗️<b>Отложенный заказ</b>\n\n\n" \
                   f"🅰️ <b>Адрес отправления:</b> {order.first_address}\n\n" \
                   f"🅱️ <b>Адрес прибытия:</b> {order.second_address}\n\n\n" \
                   f"🙋‍♂️ <b>Имя клиента:</b> {user.name}\n\n" \
                   f"📱 <b>Номер телефона клиента:</b> {user.phone}\n\n\n" \
                   f"💰 <b>Стоимость:</b> {cost} руб\n\n" \
                   f"💵 <b>Оплата:</b> {order.payment_method}\n\n" \
                   f"👶 <b>Детское кресло:</b> {order.child_seat}\n\n\n" \
                   f"💭 Комментарий к заказу: <b>{order.comment}</b>"

    await bot.send_message(callback_query.from_user.id, text=message_text,
                           reply_markup=order_acceptance_keyboard_without_propose_price(order), parse_mode='html')


@dp.callback_query_handler(lambda c: c.data.startswith('start_order_confirmation'))
async def start_order_confirmation(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[3])
    confirm_keyboard = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('✅ Подтвердить выезд', callback_data=f'order_acceptance_{order_id}'),
        InlineKeyboardButton('❌ Отмена', callback_data='otmdef')
    )
    await callback_query.message.answer(
        "⚠️ Вы хотите начать выполнение предзаказа? Пассажир получит сообщение, что Вы выехали за ним.",
        reply_markup=confirm_keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('reject_order_confirmation'))
async def reject_order_confirmation(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[3])
    confirm_keyboard = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('✅ Подтвердить отказ', callback_data=f'cancel_order_{order_id}'),
        InlineKeyboardButton('❌ Отмена', callback_data='otmdef')
    )
    await callback_query.message.answer(
        "⚠️ Вы хотите отказаться от заказа? Вы предупредили пассажира по тел., что не сможете его выполнить? При жалобе пассажира Вы можете быть заблокированы.",
        reply_markup=confirm_keyboard)


@dp.callback_query_handler(lambda c: c.data == 'otmdef')
async def cancel_action(callback_query: types.CallbackQuery):
    await callback_query.message.answer("✅ Действие отменено.")