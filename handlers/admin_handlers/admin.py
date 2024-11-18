from aiogram import types
from config_data import config
from config_data.config import ADMIN_IDS
from keyboards.inline.admin_markup import markup_admin
from loader import dp


@dp.message_handler(commands=["admin"])
async def admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer('⚠️ Ошибка! Вы не являетесь администратором!')
    else:
        await message.answer('🔑 Вы авторизованы как Админ', reply_markup=markup_admin())