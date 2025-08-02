import asyncio
import logging
from db.db import Pronouns, Punishments
from handlers import groups
from data.loader import *

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    db_pronouns = Pronouns()
    db_pronouns.createdb()
    dp.include_router(groups.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())