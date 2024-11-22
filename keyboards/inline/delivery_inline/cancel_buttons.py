from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config_data.config import ADMIN_IDS
from database.delite_from_db import delivery_delete_sent_messages
from database.get_to_db import delivery_get_sent_item_by_order, delivery_get_sent_messages, get_delivery_by_id, get_taxi, get_user
from handlers.default_handlers import start
from handlers.taxi_handlers import main_menu_taxi
from loader import dp, bot
from states.delivery_states import DeliveryStatus


def delivery_cancel_order_buttons(order_id: int) -> InlineKeyboardMarkup:
    """
    Создает кнопки для заказа
    :param order_id: ID заказа
    :return: InlineKeyboardMarkup
    """
    cancel_button = InlineKeyboardButton("❌ Отменить заказ ❌", callback_data=f"abolish_delivery_{order_id}")
    markup = InlineKeyboardMarkup(row_width=1).add(cancel_button)
    return markup

@dp.callback_query_handler(lambda c: c.data.startswith('abolish_delivery_'))
async def cancel_order(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[-1])
    confirm_markup = get_confirmation_markup(order_id)
    await bot.send_message(
        callback_query.from_user.id,
        "Вы уверены, что хотите отменить заказ?",
        reply_markup=confirm_markup
    )
    await bot.answer_callback_query(callback_query.id)

def get_special_cancel_button(order_id: int) -> InlineKeyboardMarkup:
    cancel_button = InlineKeyboardButton("❌ Отменить заказ ❌", callback_data=f"delivery_special_cancel_order_{order_id}")
    markup = InlineKeyboardMarkup(row_width=1).add(cancel_button)
    return markup


def get_confirmation_markup(order_id):
    markup = InlineKeyboardMarkup(row_width=2)
    confirm_button = InlineKeyboardButton("✅ Да, отменить", callback_data=f"cancel_delivery_{order_id}")
    deny_button = InlineKeyboardButton("❌ Нет, оставить", callback_data=f"delivery_pasdecline_cancel")
    markup.add(confirm_button, deny_button)
    return markup


async def delivery_determine_cancel_button(order) -> InlineKeyboardMarkup:
    if order.status in [DeliveryStatus.ACCEPTED, DeliveryStatus.GET_PACKAGE]:
        return get_special_cancel_button(order.id)
    else:
        return delivery_cancel_order_buttons(order.id)


@dp.callback_query_handler(lambda c: c.data.startswith('cancel_delivery_'))
async def cancel_order(callback_query: types.CallbackQuery, state: FSMContext):
    initiator_user_id = callback_query.from_user.id
    order_id = int(callback_query.data.split("_")[2])
    order = get_delivery_by_id(order_id)

    if order is None:
        await bot.send_message(callback_query.from_user.id, "Не удалось найти заказ.")
        return

    if order.status in [DeliveryStatus.COMPLETED, DeliveryStatus.CANCELED]:
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text="Заказ уже был отменен или завершен.")
        return

    busy_by = order.busy_by
    if busy_by:
        await bot.send_message(busy_by, f"😒 Заказ № {order.id} был отменен.")
        await bot.send_message(order.user_id, f"😒 Заказ № {order.id} был отменен.")

    order.status = DeliveryStatus.CANCELED
    order.save()

    taxi_id = order.taxi_id
    taxi = await get_taxi(taxi_id)

    user_id = order.user_id
    user = await get_user(user_id)

    if order.taxi_id is not None:
        if initiator_user_id not in ADMIN_IDS:  # Проверка, что инициатор не админ
            if user.rating is None:
                user.rating = 1.0  # Установите начальное значение рейтинга, если он не установлен
            else:
                user.rating = (user.rating + 1.0) / 2
            user.save()


        # await bot.send_message(order.busy_by, f"😒 Заказ № {order.id} был отменен.")
        taxi.is_busy = False
        taxi.save()

    await bot.edit_message_text(text="😔 Ваш заказ был отменен.", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)

    # Удаляем сообщения у всех таксистов
    sent_messages = delivery_get_sent_messages(order.id)
    for user_id, message_id in sent_messages:
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception as e:
            print(f"⚠️ Ошибка при удалении сообщения у пользователя {user_id}: {e}")

    delivery_delete_sent_messages(order.id)

    sent_item = delivery_get_sent_item_by_order(order)
    print(sent_item)
    if sent_item:
        await bot.delete_message(chat_id=taxi_id, message_id=sent_item.text_message_id)

    if callback_query.from_user.id in ADMIN_IDS:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="✅ Заказ отменён ")

        # Определение, кто инициировал отмену и отправка уведомления другой стороне
    if initiator_user_id == int(order.user_id):  # Если отмена инициирована пассажиром
        if order.taxi_id:
            await bot.send_message(order.taxi_id, f"😒 Заказ № {order.id} был отменен пассажиром.")
            taxi.is_busy = False
            taxi.save()
    elif initiator_user_id == order.taxi_id:  # Если отмена инициирована таксистом
        if order.user_id:
            await bot.send_message(order.user_id, f"😒 Ваш заказ № {order.id} был отменен таксистом.")

    await state.finish()

@dp.callback_query_handler(lambda call: call.data.startswith('delivery_special_cancel_order'))
async def special_cancel_order(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[-1])
    confirm_markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Да, отменить", callback_data=f"cancel_delivery_{order_id}"),
        InlineKeyboardButton("❌ Нет, оставить", callback_data=f"delivery_pasdecline_cancel_{order_id}")
    )
    await bot.send_message(
        callback_query.from_user.id,
        "🚕💨 Водитель уже выехал. Вы хотите отменить заказ? Ваш рейтинг будет снижен, возможна блокировка аккаунта.",
        reply_markup=confirm_markup
    )
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda call: call.data.startswith('delivery_pasdecline_cancel'))
async def decline_cancel_order(callback_query: types.CallbackQuery):
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text="✅Заказ остается активным.")
    await bot.answer_callback_query(callback_query.id)