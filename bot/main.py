import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from bot.logger import logger
from bot.handlers import router
from app.config import settings

async def main():
    logging.basicConfig(level=logging.INFO)
    storage = RedisStorage.from_url(settings.REDIS_URL)
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    await bot.set_my_commands([BotCommand(command="/start", description="Запустить бота")])

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())