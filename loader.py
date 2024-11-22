from aiogram import Bot, Dispatcher, types
from config_data import config
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from config_data.config import PROXY_URL

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

