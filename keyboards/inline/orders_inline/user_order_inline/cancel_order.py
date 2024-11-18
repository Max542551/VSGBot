from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config_data.config import ADMIN_IDS
from database.delite_from_db import delete_sent_messages
from database.get_to_db import get_order_by_id, get_taxi, get_sent_messages, get_user, get_sent_item_by_order
from handlers.default_handlers import start
from handlers.taxi_handlers import main_menu_taxi
from loader import dp, bot
from states.order_states import OrderStatus


def cancel_order_buttons(order_id: int) -> InlineKeyboardMarkup:
    """
    Создает кнопки для заказа
    :param order_id: ID заказа
    :return: InlineKeyboardMarkup
    """
    cancel_button = InlineKeyboardButton("❌ Отменить заказ ❌", callback_data=f"cancel_order_{order_id}")
    markup = InlineKeyboardMarkup(row_width=1).add(cancel_button)
    return markup


def get_special_cancel_button(order_id: int) -> InlineKeyboardMarkup:
    cancel_button = InlineKeyboardButton("❌ Отменить заказ ❌", callback_data=f"special_cancel_order_{order_id}")
    markup = InlineKeyboardMarkup(row_width=1).add(cancel_button)
    return markup


def get_confirmation_markup(order_id):
    markup = InlineKeyboardMarkup(row_width=2)
    confirm_button = InlineKeyboardButton("✅ Да, отменить", callback_data=f"cancel_order_{order_id}")
    deny_button = InlineKeyboardButton("❌ Нет, оставить", callback_data=f"deny_cancel_{order_id}")
    markup.add(confirm_button, deny_button)
    return markup


async def determine_cancel_button(order) -> InlineKeyboardMarkup:
    if order.status in [OrderStatus.ACCEPTED, OrderStatus.EXPECTATION]:
        return get_special_cancel_button(order.id)
    else:
        return cancel_order_buttons(order.id)


@dp.callback_query_handler(lambda c: c.data.startswith('cancel_order_'))
async def cancel_order(callback_query: types.CallbackQuery, state: FSMContext):
    initiator_user_id = callback_query.from_user.id
    order_id = int(callback_query.data.split("_")[2])
    order = get_order_by_id(order_id)

    if order is None:
        await bot.send_message(callback_query.from_user.id, "Не удалось найти заказ.")
        return

    if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELED]:
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text="Заказ уже был отменен или завершен.")
        return

    if order.deferred:
        order.deferred = False
        deferred_by = order.deferred_by
        if deferred_by:
            await bot.send_message(deferred_by, f"😒 Заказ № {order.id} был отменен.")
            await bot.send_message(order.user_id, f"😒 Заказ № {order.id} был отменен.")

    order.status = OrderStatus.CANCELED
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

        # await bot.send_message(order.taxi_id, f"😒 Заказ № {order.id} был отменен.")
        taxi.is_busy = False
        taxi.save()

    await bot.edit_message_text(text="😔 Ваш заказ был отменен.", chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)

    # Удаляем сообщения у всех таксистов
    sent_messages = get_sent_messages(order.id)
    for user_id, message_id in sent_messages:
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception as e:
            print(f"⚠️ Ошибка при удалении сообщения у пользователя {user_id}: {e}")

    delete_sent_messages(order.id)

    sent_item = get_sent_item_by_order(order)
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


@dp.callback_query_handler(lambda c: c.data.startswith('passenger_no_show_'))
async def handle_passenger_no_show(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[-1])
    order = get_order_by_id(order_id)

    if order is None:
        await bot.send_message(callback_query.from_user.id, "Не удалось найти заказ.")
        return

    confirm_markup = get_confirmation_markup(order_id)  # Используем новую функцию для создания клавиатуры

    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                text="⚠️ Вы позвонили пассажиру? Поездка будет отменена, рейтинг пассажира будет понижен. Вы уверены?",
                                reply_markup=confirm_markup)


@dp.callback_query_handler(lambda c: c.data.startswith('deny_cancel_'))
async def handle_deny_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = int(callback_query.data.split("_")[-1])  # Получаем ID заказа
    order = get_order_by_id(order_id)

    if order is None:
        await bot.send_message(callback_query.from_user.id, "Не удалось найти заказ.")
        return

    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text="❌ Отмена заказа отклонена. Продолжаем поездку.")

    # Сброс состояния
    await state.reset_state()

    await main_menu_taxi.main_menu_taxi(
        callback_query.message)  # Замените start.start на вашу функцию для отображения главного меню


@dp.callback_query_handler(lambda call: call.data.startswith('special_cancel_order_'))
async def special_cancel_order(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split("_")[-1])
    confirm_markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("✅ Да, отменить", callback_data=f"cancel_order_{order_id}"),
        InlineKeyboardButton("❌ Нет, оставить", callback_data=f"pasdecline_cancel_{order_id}")
    )
    await bot.send_message(
        callback_query.from_user.id,
        "🚕💨 Водитель уже выехал. Вы хотите отменить заказ? Ваш рейтинг будет снижен, возможна блокировка аккаунта.",
        reply_markup=confirm_markup
    )
    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda call: call.data.startswith('pasdecline_cancel_'))
async def decline_cancel_order(callback_query: types.CallbackQuery):
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text="✅Заказ остается активным.")
    await bot.answer_callback_query(callback_query.id)
