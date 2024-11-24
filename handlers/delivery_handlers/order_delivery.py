from ast import Del
import asyncio
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.add_to_db import save_sent_delivery_messages
from database.delite_from_db import delivery_delete_sent_messages
from database.get_to_db import delivery_get_sent_messages, get_delivery_by_id, get_taxi, get_user
from handlers.taxi_handlers import main_menu_taxi
from keyboards.inline.delivery_inline.cancel_buttons import delivery_cancel_order_buttons
from keyboards.inline.delivery_inline.reply_accept_the_delivery import delivery_acceptance_keyboard_without_propose_price
from keyboards.reply import reply_menu_user
from loader import dp, bot
from states.delivery_states import DeliveryStatus
from aiogram.dispatcher import FSMContext


@dp.callback_query_handler(lambda c: 'delivery_order_acceptance' in c.data)
async def process_order_defer(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    order_id = int(callback_query.data.split('_')[-1])
    taxi_id = callback_query.from_user.id
    taxi = await get_taxi(taxi_id)
    order = get_delivery_by_id(order_id)
    print(order_id)
    print(order.busy_by)

    if order.busy_by:
        # await bot.edit_message_text(text="⛔️ Заказ уже принят другим водителем",
        #                             chat_id=callback_query.message.chat.id,
        #                             message_id=callback_query.message.message_id)
        return

    # order.status = DeliveryStatus.ACCEPTED
    order.busy_by = taxi_id
    order.save()
    await bot.edit_message_text(text="✅ Доставка принята\n\n"
                                     "Перейдите в 🏡 Главное меню для просмотра информации",
                                chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id)
    await bot.send_message(order.user_id,
                           f"✅ Водитель <b>{taxi.name}</b> принял ваш заказ и выполнит в назначенное время!\n\n"
                           f"Перейдите в 🏠 Главное меню для просмотра информации об доставке",
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

@dp.callback_query_handler(lambda c: c.data.startswith('user_delivery_orders'), state="*")
async def process_delivery_order_for_user(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    order_id = int(callback_query.data.split('_')[3])
    order = get_delivery_by_id(order_id)
    if order.status == DeliveryStatus.CANCELED or order.status == DeliveryStatus.COMPLETED:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Заказ был уже выполнен, либо отменен\n\n")
        return

    taxi = await get_taxi(order.busy_by)
    cost = "Ждет предложения" if order.cost is None else f"{order.cost} руб"
    package_price = f"💰 <b>Сколько стоит посылка:</b> {order.package_price}\n\n" if order.package_price else ""
    message_text = f"❗️<b>Доставка</b>\n\n\n" \
                   f"👨 <b>Имя водителя:</b> {taxi.name if taxi else 'в поиске'}\n\n" \
                   f"📈 <b>Рейтинг водителя:</b> {taxi.rating if taxi else 'в поиске'}\n\n" \
                   f"📱 <b>Телефон водителя:</b> {taxi.phone if taxi else 'в поиске'}\n\n\n" \
                   f"🅰️ <b>Адрес отправления:</b> {order.first_address}\n\n" \
                   f"🅱️ <b>Адрес прибытия:</b> {order.second_address}\n\n\n" \
                   f"💰 <b>Стоимость:</b> {cost}\n\n" \
                   f"💵 <b>Оплата:</b> {order.payment_method}\n\n" \
                   f"📦 <b>Оплата посылки:</b> {order.package_payment}\n\n" \
                   f"{package_price}" \
                   f"💍 <b>Содержимое посылки</b> {order.package_content}\n\n" \
                   f"💭 Комментарий к заказу: <b>{order.comment}</b>"

    await bot.send_message(callback_query.from_user.id, text=message_text, reply_markup=delivery_cancel_order_buttons(order_id),
                           parse_mode='html')


@dp.callback_query_handler(lambda c: c.data.startswith('delivery_order'))
async def process_delivery_order(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    order_id = int(callback_query.data.split('_')[-1])

    order = get_delivery_by_id(order_id)

    if order.status == DeliveryStatus.CANCELED or order.status == DeliveryStatus.COMPLETED:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Заказ был уже выполнен, либо отменен\n\n")

        return

    user = await get_user(order.user_id)
    cost = order.cost
    
    package_price = f"💰 <b>Сколько стоит посылка:</b> {order.package_price}\n\n" if order.package_price else ""
    message_text = f"❗️<b>Доставка</b>\n\n\n" \
                   f"🅰️ <b>Адрес отправления:</b> {order.first_address}\n\n" \
                   f"🅱️ <b>Адрес прибытия:</b> {order.second_address}\n\n\n" \
                   f"🙋‍♂️ <b>Имя клиента:</b> {user.name}\n\n" \
                   f"📱 <b>Номер телефона клиента:</b> {user.phone}\n\n\n" \
                   f"💰 <b>Стоимость:</b> {cost}\n\n" \
                   f"💵 <b>Оплата:</b> {order.payment_method}\n\n" \
                   f"📦 <b>Оплата посылки:</b> {order.package_payment}\n\n" \
                   f"{package_price}" \
                   f"💍 <b>Содержимое посылки</b> {order.package_content}\n\n" \
                   f"💭 Комментарий к заказу: <b>{order.comment}</b>"

    await bot.send_message(callback_query.from_user.id, text=message_text,
                           reply_markup=delivery_acceptance_keyboard_without_propose_price(order), parse_mode='html')


@dp.callback_query_handler(lambda c: c.data.startswith('delivery_start_order_confirmation'), state="*")
async def start_order_confirmation(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    confirm_keyboard = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('✅ Подтвердить выезд', callback_data=f'delivery_departure_acceptance_{order_id}'),
        InlineKeyboardButton('❌ Отмена', callback_data=f'otmdef')
    )
    await callback_query.message.answer(
        "⚠️ Вы хотите начать выполнение доставки? Заказчик получит сообщение, что вы выехали.",
        reply_markup=confirm_keyboard)

@dp.callback_query_handler(lambda c: 'delivery_departure_acceptance' in c.data, state="*")
async def process_delivery_acceptance(callback_query: types.CallbackQuery, state: FSMContext):
    print("cstta")
    order_id = int(callback_query.data.split("_")[-1])
    taxi_id = callback_query.from_user.id
    taxi = await get_taxi(taxi_id)
    order = get_delivery_by_id(order_id)

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

    await bot.send_message(
        chat_id=order.user_id,
        text=f"🥳 Доставщик найден!\n\n"
                "🚕 Доставщик выехал\n\n"
                "Нажмите кнопку 🏠 Главное меню чтобы посмотреть информацию",
        reply_markup=reply_menu_user.get_main_menu_keyboard(), parse_mode='html')

    if order.status == DeliveryStatus.CANCELED or order.status == DeliveryStatus.COMPLETED:
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
    order.status = DeliveryStatus.ACCEPTED
    order.save()

    taxi.shift_count += 1
    taxi.is_busy = True
    taxi.save()

    # Удаляем сообщения у всех таксистов
    sent_messages = delivery_get_sent_messages(order.id)
    for user_id, message_id in sent_messages:
        if user_id != taxi_id:
            try:
                await bot.delete_message(chat_id=user_id, message_id=message_id)
                await asyncio.sleep(0.2)
            except Exception as e:
                print(f"⚠️ Ошибка при удалении сообщения у пользователя(принятие заказа) {user_id}: {e}")

    delivery_delete_sent_messages(order.id)

    # Изменение текста сообщения
    await bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text="✅ Вы приняли заказ!")

    await main_menu_taxi.main_menu_taxi(callback_query.message)

    await state.finish()
    await bot.answer_callback_query(callback_query.id)



@dp.callback_query_handler(lambda c: c.data.startswith('delivery_reject_order_confirmation'), state="*")
async def reject_order_confirmation(callback_query: types.CallbackQuery):
    order_id = int(callback_query.data.split('_')[-1])
    confirm_keyboard = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('✅ Подтвердить отказ', callback_data=f'cancel_delivery_{order_id}'),
        InlineKeyboardButton('❌ Отмена', callback_data='otmdef')
    )
    await callback_query.message.answer(
        "⚠️ Вы хотите отказаться от заказа? Вы предупредили заказчика по тел., что не сможете его выполнить? При жалобе заказчика Вы можете быть заблокированы.",
        reply_markup=confirm_keyboard)


@dp.callback_query_handler(lambda c: c.data == 'otmdef')
async def cancel_action(callback_query: types.CallbackQuery):
    await callback_query.message.answer("✅ Действие отменено.")