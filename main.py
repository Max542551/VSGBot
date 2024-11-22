import asyncio
import logging
from operator import le
from loader import dp, bot
import handlers  # Handlers import after dp
from utils.set_bot_commands import set_default_commands
from utils.shifts import check_shifts


async def main():
    await set_default_commands(dp)
    asyncio.create_task(check_shifts())
    await dp.start_polling(bot, allowed_updates=["message", "inline_query", "callback_query"])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
