from datetime import datetime

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config_data.config import group_id
from database.get_to_db import get_taxi
from handlers.taxi_handlers import main_menu_taxi
from loader import dp, bot


@dp.callback_query_handler(lambda c: c.data == 'change_shift')
async def process_toggle_active_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    taxi = await get_taxi(user_id)

    if taxi:
        if taxi.admin_deactivated:
            await bot.answer_callback_query(callback_query.id, show_alert=True,
                                            text="🚫 Ваш аккаунт заблокирован администратором!")
            return

        # if taxi.is_watching:
        #     await bot.answer_callback_query(callback_query.id, show_alert=True,
        #                                     text="⚠️ Для начала смены, выключите режим наблюдения!\n\n")
        #     return

        if taxi.shift:
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("✅ Подтвердить", callback_data='end_shift'),
                InlineKeyboardButton("❌ Отклонить", callback_data='secline_end_shift')
            )
            await bot.edit_message_text(text="❗️Вы уверены, что хотите завершить смену?",
                                        chat_id=callback_query.from_user.id,
                                        message_id=callback_query.message.message_id, reply_markup=markup)
        else:
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("✅ Подтвердить", callback_data='start_shift'),
                InlineKeyboardButton("❌ Отклонить", callback_data='secline_start_shift')
            )
            await bot.edit_message_text(text="❗️Начинаем работать? \n\n" 
                                        " Будет списана комиссия 30 руб.",
                                        chat_id=callback_query.from_user.id,
                                        message_id=callback_query.message.message_id,
                                        reply_markup=markup)
    else:
        await bot.answer_callback_query(callback_query.id, "⚠️ Вы не являетесь водителем.")


# Функции подтверждения и отклонения
async def process_start_shift_confirmation(callback_query: types.CallbackQuery):
    # await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    taxi = await get_taxi(user_id)
    commission = 30

    if taxi.balance <= 0 or taxi.balance < commission:
        await bot.answer_callback_query(callback_query.id, show_alert=True,
                                        text="⛔️ Недостаточно средств для начала смены!\n\n")
        return

    if taxi:
        taxi.balance -= commission
        taxi.shift = True
        taxi.shift_start_time = datetime.now()
        taxi.save()
        # код для списания суммы с баланса
        await bot.edit_message_text(text="👍 Смена начата", chat_id=callback_query.from_user.id,
                                    message_id=callback_query.message.message_id)
        await bot.send_message(group_id, f'❗<b>{taxi.name} {taxi.car} {taxi.registration_number}</b> начал смену. Баланс - <b>{taxi.balance}</b> руб', parse_mode='html')

        await main_menu_taxi.main_menu_taxi(callback_query.message)


async def process_end_shift_confirmation(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    taxi = await get_taxi(user_id)
    if taxi:
        taxi.shift_count = 0
        taxi.shift = False
        taxi.shift_start_time = None
        taxi.save()
        await bot.edit_message_text(text="👍 Смена завершена", chat_id=callback_query.from_user.id,
                                    message_id=callback_query.message.message_id)
        await bot.send_message(group_id, f'❗<b>{taxi.name} {taxi.car} {taxi.registration_number}</b> завершил смену. Баланс - <b>{taxi.balance}</b> руб', parse_mode='html')

        await main_menu_taxi.main_menu_taxi(callback_query.message)


# обработчики для подтверждения начала и завершения смены
@dp.callback_query_handler(lambda c: c.data == 'start_shift')
async def confirm_start_shift(callback_query: types.CallbackQuery):
    await process_start_shift_confirmation(callback_query)


@dp.callback_query_handler(lambda c: c.data == 'end_shift')
async def confirm_end_shift(callback_query: types.CallbackQuery):
    await process_end_shift_confirmation(callback_query)


@dp.callback_query_handler(lambda c: c.data == 'secline_end_shift')
async def confirm_start_shift(callback_query: types.CallbackQuery):
    await bot.edit_message_text(text="🕰️ Еще поработаем", chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id)
    await main_menu_taxi.main_menu_taxi(callback_query.message)


@dp.callback_query_handler(lambda c: c.data == 'secline_start_shift')
async def confirm_end_shift(callback_query: types.CallbackQuery):
    await bot.edit_message_text(text="🕰️ Еще отдыхаем", chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id)
    await main_menu_taxi.main_menu_taxi(callback_query.message)

# @dp.callback_query_handler()

