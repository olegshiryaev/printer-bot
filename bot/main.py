import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.http import client
from bot.handlers import start, search, callbacks
# from bot.middlewares.clear_state import ClearStaleStateMiddleware

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# dp.message.middleware(ClearStaleStateMiddleware(timeout=600))

dp.include_routers(start.router, search.router, callbacks.router)


async def on_shutdown():
    await client.aclose()


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown()


if __name__ == "__main__":
    asyncio.run(main())