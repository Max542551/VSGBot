from aiogram import types
from aiogram.dispatcher import FSMContext
from database.add_to_db import save_sent_messages
from database.get_to_db import get_order_by_id, get_taxi
from handlers.default_handlers import start
from keyboards.inline.orders_inline.user_order_inline.accept_or_decline_price import accept_or_decline_price_keyboard
from loader import dp, bot
from states.order_states import ProposePriceState

from config_data.config import min_price


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('order_propose_price'))
async def process_propose_price_callback(callback_query: types.CallbackQuery):
    order_id = callback_query.data.split('_')[-1]
    state = dp.current_state(user=callback_query.from_user.id)
    taxi_id = callback_query.from_user.id
    taxi = await get_taxi(taxi_id)
    if taxi:
        if taxi.balance < 10:
            await bot.answer_callback_query(callback_query.id, show_alert=True,
                                            text="⚠️ Вы не можете предложить цену, необходимо пополнить баланс в меню")
            return

    await state.set_state(ProposePriceState.price)
    await state.update_data(order_id=order_id)

    # Обновляем сообщение, удаляя кнопку "Предложить цену"
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id,
                                        message_id=callback_query.message.message_id)

    await bot.send_message(callback_query.from_user.id, '💰 Введите вашу цену:')


@dp.message_handler(state=ProposePriceState.price, content_types=types.ContentType.TEXT)
async def process_propose_price(message: types.Message, state: FSMContext):
    if message.text.startswith('🏠 Главное меню'):
        await start.start(message, state)
        return

    try:
        price = int(message.text)
        if price <= min_price:
            await bot.send_message(message.chat.id, f"Минимальная стоимость поездки по городу {min_price} руб. Пожалуйста введите сумму равную или больше минимальной")
            return

        taxi_id = message.from_user.id
        async with state.proxy() as data:
            order_id = data['order_id']
        order = get_order_by_id(order_id)
        taxi = await get_taxi(taxi_id)

        if taxi is None:
            await bot.send_message(taxi_id, "⚠️ Ошибка: водитель не найден.")
            return

        await bot.send_message(message.from_user.id, f"✅ Предложение цены {price} руб отправлено клиенту")
        message = await bot.send_message(order.user_id,
                                         f'🔔 Водитель <b>{taxi.name}</b> на <b>{taxi.color_car}</b> <b>{taxi.car}</b> c рейтингом {round(taxi.rating, 2)} предлагает цену <b>{price}</b> руб за ваш заказ',
                                         reply_markup=accept_or_decline_price_keyboard(order, taxi_id, price),
                                         parse_mode='html')


    # Save sent message
        save_sent_messages(order.id, [(order.user_id, message.message_id)])
    except ValueError:
        await message.answer("⚠️ Введите корректную цену, только числа")

    await state.finish()
