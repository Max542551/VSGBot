import asyncio
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.add_to_db import save_sent_delivery_messages, save_sent_messages
from database.delite_from_db import delete_sent_messages
from database.get_to_db import delivery_get_sent_messages, get_delivery_by_id, get_order_by_id, get_taxi, get_sent_messages
from handlers.taxi_handlers import main_menu_taxi
from loader import dp, bot
from states.delivery_states import DeliveryStatus
from states.order_states import OrderStatus

def delivery_send_confirmation_buttons(taxi_id, order_id, price):
    print("тту блыо")
    markup = InlineKeyboardMarkup(row_width=2)
    item1 = InlineKeyboardButton("✅ Подтвердить", callback_data=f'delivery_confirm_{order_id}_{taxi_id}_{price}')
    item2 = InlineKeyboardButton("❌ Отказаться", callback_data=f'delivery_decline_{order_id}_{taxi_id}')
    markup.add(item1, item2)

    return markup

@dp.callback_query_handler(lambda c: 'delivery_confirm_' in c.data, state="*")
async def process_delivery_order(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    _, _, order_id, taxi_id, price = callback_query.data.split("_", 4)
    order_id = int(order_id)
    taxi_id = int(taxi_id)
    price = int(price)
    taxi = await get_taxi(taxi_id)

    order = get_delivery_by_id(order_id)
    order.cost = price
    order.busy_by = taxi_id
    order.status = DeliveryStatus.ACCEPTED
    order.save()
    await bot.edit_message_text(text="✅ Доставка принята\n\n"
                                     "Перейдите в 🏡 Главное меню для просмотра информации",
                                chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    await bot.send_message(order.user_id,
                           f"✅ Водитель <b>{taxi.name}</b> принял ваш заказ и выполнит в назначенное время!\n\n"
                           f"Перейдите в 🏠 Главное меню для просмотра информации об отложенном заказе",
                           parse_mode='html')

    # Удалить сообщения у всех таксистов, кроме того, который отложил заказ
    sent_messages = delivery_get_sent_messages(order_id)
    for user_id, message_id in sent_messages:
        if user_id != taxi_id:
            await bot.delete_message(chat_id=user_id, message_id=message_id)

    # Обновить сохраненные сообщения, чтобы оставить только сообщение для таксиста, который отложил заказ
    try:
        save_sent_delivery_messages(order_id, [(taxi_id, message_id)])
    except UnboundLocalError:
        pass
    
# обработка нажатия кнопки "Отказаться"
@dp.callback_query_handler(lambda c: c.data.startswith('delivery_decline_'), state="*")
async def process_decline_callback(callback_query: types.CallbackQuery):
    _, _, order_id, taxi_id = callback_query.data.split("_", 3)
    order_id = int(order_id)
    order = get_delivery_by_id(order_id)

    await bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text="❌ Вы отказались от заказа.")

    await bot.send_message(order.user_id, "❌ Водитель отказался от выполнения вашего заказа.\n\n"
                                          "Ждём предложения от других водителей. Если хотите отменить заказ, нажмите кнопку 🏠 Главное меню")
