import os
from dotenv import load_dotenv, find_dotenv
from geopy import Photon
from geopy.adapters import AioHTTPAdapter
from peewee import SqliteDatabase

group_id = '-1002131610863'

test_value = ""

database = SqliteDatabase('database/Taxi.db')

geolocator = Photon(user_agent="geoapiExercises", adapter_factory=AioHTTPAdapter, timeout=5)


# PROXY_URL = "http://proxy.server:3128"

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
    load_dotenv()

# Инициализируем бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
ADMIN_IDS = [int(admin_id) for admin_id in ADMIN_ID.split(",")]


