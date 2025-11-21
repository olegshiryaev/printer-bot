import asyncio
import functools
from aiogram.exceptions import TelegramRetryAfter


def anti_flood(func):
    """
    Декоратор антифлуда: ловит RetryAfter и ждёт нужное время.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            return await func(*args, **kwargs)

    return wrapper
