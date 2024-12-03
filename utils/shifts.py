import asyncio
from datetime import datetime, timedelta

from config_data.config import group_id
from database.database import Taxi
from loader import bot


async def check_shifts():
    while True:
        now = datetime.now()
        for taxi in Taxi.select().where(Taxi.shift == True):
            if taxi.shift_start_time:
                if taxi.shift_start_time + timedelta(hours=7) <= now:
                    taxi.shift_count = 0
                    taxi.shift = False
                    taxi.shift_start_time = None
                    taxi.save()
                    await bot.send_message(group_id, f'❗ У <b>{taxi.name} {taxi.car} {taxi.registration_number}</b> смена закончена автоматически', parse_mode='html')

                    await bot.send_message(taxi.user_id, "❗ Ваша смена автоматически завершена после 7 часов работы ❗\n\n"
                                                         "Для продолжения работы начните смену снова")
        await asyncio.sleep(600)  # Проверка каждые 10 минут
