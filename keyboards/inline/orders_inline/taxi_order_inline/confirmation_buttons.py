import asyncio
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.add_to_db import save_sent_messages
from database.delite_from_db import delete_sent_messages
from database.get_to_db import get_order_by_id, get_taxi, get_sent_messages
from handlers.taxi_handlers import main_menu_taxi
from loader import dp, bot
from states.order_states import OrderStatus


def send_confirmation_buttons(taxi_id, order_id, price):
    markup = InlineKeyboardMarkup(row_width=2)
    item1 = InlineKeyboardButton("✅ Подтвердить", callback_data=f'confirm_{order_id}_{taxi_id}_{price}')
    item2 = InlineKeyboardButton("❌ Отказаться", callback_data=f'decline_{order_id}_{taxi_id}')
    markup.add(item1, item2)

    return markup


def send_confirmation_buttons_def(taxi_id, order_id, price):
    markup = InlineKeyboardMarkup(row_width=2)
    item1 = InlineKeyboardButton("✅ Принять предзаказ", callback_data=f'defrconfirm_{order_id}_{taxi_id}_{price}')
    item2 = InlineKeyboardButton("❌ Отказаться", callback_data=f'decline_{order_id}_{taxi_id}')
    markup.add(item1, item2)

    return markup


@dp.callback_query_handler(lambda c: 'defrconfirm_' in c.data)
async def process_order_defer(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    _, order_id, taxi_id, price = callback_query.data.split("_", 3)
    order_id = int(order_id)
    taxi_id = int(taxi_id)
    price = int(price)
    taxi = await get_taxi(taxi_id)

    order = get_order_by_id(order_id)
    order.cost = price
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


@dp.callback_query_handler(lambda c: c.data.startswith('confirm_'))
async def process_confirm_callback(callback_query: types.CallbackQuery):
    _, order_id, taxi_id, price = callback_query.data.split("_", 3)
    order_id = int(order_id)
    taxi_id = int(taxi_id)
    price = int(price)
    taxi = await get_taxi(taxi_id)

    if taxi.balance <= 0:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Недостаточно средств для принятия заказа!\n\n")
        return

    if taxi.is_busy:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Вы уже приняли другой заказ.\n\n")
        return

    order = get_order_by_id(order_id)

    if order.taxi_id is not None:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="🤷‍♂️ Заказ уже был принят другим таксистом."
        )
        return

    order.taxi_id = taxi_id
    order.cost = price
    order.status = OrderStatus.ACCEPTED
    order.save()

    taxi.shift_count += 1
    taxi.is_busy = True
    taxi.save()

    # Удаляем сообщения у всех таксистов
    sent_messages = get_sent_messages(order.id)
    for user_id, message_id in sent_messages:
        if user_id != taxi_id:
            try:
                await bot.delete_message(chat_id=user_id, message_id=message_id)
                await asyncio.sleep(0.2)
            except Exception as e:
                print(f"⚠️ Ошибка при удалении сообщения у пользователя(принятие цены) {user_id}: {e}")

    delete_sent_messages(order.id)

    await bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text="✅ Вы подтвердили заказ!")

    await main_menu_taxi.main_menu_taxi(callback_query.message)

    await bot.send_message(order.user_id,
                           "🚕 Водитель выехал к вам\n\n"
                           "Нажмите кнопку 🏠 Главное меню чтобы посмотреть информацию")


# обработка нажатия кнопки "Отказаться"
@dp.callback_query_handler(lambda c: c.data.startswith('decline_'))
async def process_decline_callback(callback_query: types.CallbackQuery):
    _, order_id, taxi_id = callback_query.data.split("_", 2)
    order_id = int(order_id)
    order = get_order_by_id(order_id)

    await bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text="❌ Вы отказались от заказа.")

    await bot.send_message(order.user_id, "❌ Водитель отказался от выполнения вашего заказа.\n\n"
                                          "Ждём предложения от других водителей. Если хотите отменить заказ, нажмите кнопку 🏠 Главное меню")
