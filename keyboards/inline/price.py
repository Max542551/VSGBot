from aiogram import types

from loader import dp, bot

price_list = """
Бот не устанавливает цен и тарифов. Цена поездки оговаривается непосредственно между участниками поездки индивидуально.
В ближайшее время в данном разделе появится РЕКОМЕНДОВАННЫЙ прайс по городу и межгород.

Приятной поездки 🚕

"""


@dp.callback_query_handler(lambda c: c.data == 'price')  # добавляем обработчик нажатия на кнопку
async def send_price_list(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(chat_id=callback_query.from_user.id, text=price_list, parse_mode='html')
