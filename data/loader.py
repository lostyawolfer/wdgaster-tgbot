from aiogram import Bot, Dispatcher
from data.config import configfile
bot = Bot(configfile["TOKEN"])
dp = Dispatcher(bot=bot)