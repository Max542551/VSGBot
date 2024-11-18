from aiogram import types
from database.get_to_db import get_order_by_id, get_taxi
from keyboards.inline.orders_inline.taxi_order_inline.confirmation_buttons import send_confirmation_buttons, \
    send_confirmation_buttons_def
from loader import dp, bot


@dp.callback_query_handler(lambda c: c.data.startswith('acceptprice_'))
async def process_accept_price_callback(callback_query: types.CallbackQuery):
    _, order_id, taxi_id, price = callback_query.data.split("_", 3)
    order_id = int(order_id)
    taxi_id = int(taxi_id)
    user_id = callback_query.from_user.id

    order = get_order_by_id(order_id)
    if order is None:
        await bot.send_message(user_id, "😔 Не удалось найти заказ.")
        return

    taxi = await get_taxi(taxi_id)
    if taxi is None:
        await bot.send_message(user_id, "⚠️ Ошибка: водитель не найден.")
        return

    await bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=f"✅ Вы приняли предложение по цене {price} руб от водителя {taxi.name}!\n\n"
             f"Дождитесь подтверждение заказа от водителя\n")

    if order.deferred:
        await bot.send_message(
            chat_id=taxi_id,
            text=f"🥳 Пользователь принял ваше предложение по цене {price} руб!",
            reply_markup=send_confirmation_buttons_def(taxi_id, order_id, price))
    else:
        # отправляем уведомление водителю
        await bot.send_message(
            chat_id=taxi_id,
            text=f"🥳 Пользователь принял ваше предложение по цене {price} руб!", reply_markup=send_confirmation_buttons(taxi_id, order_id, price))

    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('declineprice'))
async def process_decline_price_callback(callback_query: types.CallbackQuery):
    _, order_id, taxi_id, price = callback_query.data.split("_", 3)

    order_id = int(order_id)
    user_id = callback_query.from_user.id

    order = get_order_by_id(order_id)
    if order is None:
        await bot.send_message(user_id, "😔 Не удалось найти заказ.")
        return

    taxi = await get_taxi(taxi_id)
    if taxi is None:
        await bot.send_message(user_id, "⚠️ Ошибка: водитель не найден.")
        return

    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=f'😤 Вы отклонили предложение водителя <b>{taxi.name}</b> с ценой <b>{price} руб</b>\n\n'
                                     f'Ждём предложения от других водителей. Если хотите отменить заказ, нажмите кнопку 🏠 Главное меню',
                                reply_markup=None, parse_mode='html')

    await bot.send_message(chat_id=taxi_id,
                           text=f'😔 Ваше предложение c ценой <b>{price}</b> по заказу <b>{order_id}</b> было отклонено.\n\n'
                                f'Теперь вы можете принять заказ только на условиях клиента!', parse_mode='html')
