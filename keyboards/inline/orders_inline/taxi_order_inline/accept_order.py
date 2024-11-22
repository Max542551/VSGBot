import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext

from database.delite_from_db import delete_sent_messages
from database.get_to_db import get_order_by_id, get_taxi, get_sent_messages
from handlers.taxi_handlers import main_menu_taxi
from keyboards.reply import reply_menu_user
from loader import bot, dp
from states.order_states import OrderStatus


@dp.callback_query_handler(lambda c: c.data.startswith('order_acceptance_'))
async def process_order_acceptance(callback_query: types.CallbackQuery, state: FSMContext):
    order_id = int(callback_query.data.split("_")[2])
    taxi_id = callback_query.from_user.id
    taxi = await get_taxi(taxi_id)
    order = get_order_by_id(order_id)

    if order is None:
        await bot.send_message(taxi_id, "😔 Не удалось найти заказ.")
        return

    if taxi.is_busy:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Вы уже приняли другой заказ.\n\n")
        return

    if order.taxi_id is not None:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="🤷‍♂️ Заказ уже был принят другим таксистом."
        )
        return

    if order.deferred:
        await bot.send_message(
            chat_id=order.user_id,
            text=f"🚕 Водитель выехал к вам\n\n"
                 "Нажмите кнопку 🏠 Главное меню чтобы посмотреть информацию",
            reply_markup=reply_menu_user.get_main_menu_keyboard(), parse_mode='html')
    else:
        await bot.send_message(
            chat_id=order.user_id,
            text=f"🥳 Автомобиль найден!\n\n"
                 "🚕 Водитель выехал к вам\n\n"
                 "Нажмите кнопку 🏠 Главное меню чтобы посмотреть информацию",
            reply_markup=reply_menu_user.get_main_menu_keyboard(), parse_mode='html')

    if order.deferred:
        order.deferred = False
        order.save()

    if order.status == OrderStatus.CANCELED or order.status == OrderStatus.COMPLETED:
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⛔️ Заказ был отменен."
        )
        return


    if taxi.balance <= 0:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Недостаточно средств для принятия заказа!\n\n")
        return

    order.taxi_id = taxi_id
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
                print(f"⚠️ Ошибка при удалении сообщения у пользователя(принятие заказа) {user_id}: {e}")

    delete_sent_messages(order.id)

    # Изменение текста сообщения
    await bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text="✅ Вы приняли заказ!")

    await main_menu_taxi.main_menu_taxi(callback_query.message)

    await state.finish()
    await bot.answer_callback_query(callback_query.id)
