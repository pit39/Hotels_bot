from dotenv import load_dotenv
from rapidapi import RapidAPIRequests
import os
import telebot
from telebot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE
from database import *

load_dotenv()

bot_token = os.getenv('BOT_TOKEN')
rapid_api_key = os.getenv("RAPIDAPI_KEY")
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_PORT = os.getenv('WEBHOOK_PORT')  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = os.getenv('WEBHOOK_LISTEN')  # In some VPS you may need to put here the IP address
# WEBHOOK_SSL_CERT = os.getenv(WEBHOOK_SSL_CERT)  # Path to the ssl certificate
# WEBHOOK_SSL_PRIV = os.getenv(WEBHOOK_SSL_PRIV)  # Path to the ssl private key

max_hotels = 20  # Максимум выводимых отелей
max_photos = 10  # Максимум выводимых фотографий
max_history = 10  # Максимум выводимых запросов истории

bot = telebot.TeleBot(bot_token)

api_getter = RapidAPIRequests(rapid_api_key)

calendar = Calendar(language=RUSSIAN_LANGUAGE)
calendar_1_callback = CallbackData("calendar_1", "action", "year", "month", "day")

User.create_table()
City.create_table()
Hotel.create_table()
History.create_table()
