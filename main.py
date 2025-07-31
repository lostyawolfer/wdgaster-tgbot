import asyncio
import logging
from db.db import Pronouns, Punishments
from handlers import user_menu
from data.loader import *

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # db_punishments = Punishments()
    # db_punishments.createdb()
    db_pronouns = Pronouns()
    db_pronouns.createdb()
    dp.include_router(user_menu.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())