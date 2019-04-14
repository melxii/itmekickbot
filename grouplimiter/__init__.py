import logging
import configparser
from telethon import TelegramClient
from .sqlite import Database

logging.basicConfig(level=logging.INFO)


config = configparser.ConfigParser()
config.read("config.ini")


API_ID = config.getint("TELEGRAM", "api_id")
API_HASH = config.get("TELEGRAM", "api_hash")
TOKEN = config.get("TELEGRAM", "token")

bot = TelegramClient("grouplimiterbot", API_ID, API_HASH)
db = Database("data.db")


bot.start(bot_token=TOKEN)
