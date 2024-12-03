from aiogram import types
from aiogram.dispatcher import filters

from loader import dp, bot


def generate_support_button():
    return types.InlineKeyboardButton('👥 Поддержка', callback_data='support')


@dp.callback_query_handler(filters.Text(equals='support'))
async def support_callback_handler(query: types.CallbackQuery):
    support_message = f"""
Сервис представляет собой автоматизированную площадку, на которой водители (частные лица) и пассажиры договариваются о поездке: 

Пассажир указывает желаемый пункт отправления и назначения, все активные водители получают информацию о заказе принимают и назначают цену или игнорирую его.

Если у Вас возникли вопросы или предложения по работе сервиса пожалуйста пишите в личные сообщения админу группы. Чтобы узнавать новости сервиса подпишитесь на группу Тех поддержки.

Техническая поддержка - https://t.me/podderzhka_VSG_Melenki  
Администратор группы - https://t.me/Bot_Taxi_Vsg

    """

    await bot.send_message(chat_id=query.from_user.id, text=support_message, parse_mode='HTML')
