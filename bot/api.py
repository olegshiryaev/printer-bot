import asyncio
from typing import Optional, Dict, Any
import httpx
from loguru import logger
from app.config import settings
from bot.cache import AsyncLRU, async_lru_cache_decorator

# Локальный кэш
cache = AsyncLRU(maxsize=2000)

# Простая функция retry с экспоненциальным бэкоффом
async def _request_with_retry(method: str, url: str, params: dict = None, timeout: float = 10.0, retries: int = 2):
    last_exc = None
    backoff = 0.2
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.request(method, url, params=params)
                resp.raise_for_status()
                return resp.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_exc = e
            logger.warning("API request failed %s %s (attempt %d): %s", method, url, attempt, e)
            await asyncio.sleep(backoff)
            backoff *= 2
    logger.error("API request ultimately failed %s %s: %s", method, url, last_exc)
    return None


@async_lru_cache_decorator(cache)
async def search_printers(q: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
    url = f"{settings.API_BASE}/printers"
    params = {"q": q, "page": page, "limit": limit}
    data = await _request_with_retry("GET", url, params=params)
    if data is None:
        return {"items": [], "total": 0, "error": "unreachable"}
    return data


@async_lru_cache_decorator(cache)
async def search_cartridges(q: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
    url = f"{settings.API_BASE}/cartridges"
    params = {"q": q, "page": page, "limit": limit}
    data = await _request_with_retry("GET", url, params=params)
    if data is None:
        return {"items": [], "total": 0, "error": "unreachable"}
    return data


@async_lru_cache_decorator(cache)
async def get_printer(printer_id: int) -> Optional[Dict[str, Any]]:
    url = f"{settings.API_BASE}/printer/{printer_id}"
    return await _request_with_retry("GET", url)


@async_lru_cache_decorator(cache)
async def get_cartridge(cartridge_id: int) -> Optional[Dict[str, Any]]:
    url = f"{settings.API_BASE}/cartridge/{cartridge_id}"
    return await _request_with_retry("GET", url)