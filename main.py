import asyncio
from handlers import user_menu
from data.loader import *

async def main():
    dp.include_router(user_menu.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())