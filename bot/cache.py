import asyncio
from typing import Any, Dict, List, Tuple

class AsyncLRU:
    """Простой потокобезопасный LRU-кэш для асинхронного кода."""
    def __init__(self, maxsize: int = 1024):
        self.maxsize = maxsize
        self.cache: Dict[Any, Any] = {}
        self.order: List[Any] = []
        self.lock = asyncio.Lock()

    async def get(self, key: Any):
        async with self.lock:
            if key in self.cache:
                # move to front
                try:
                    self.order.remove(key)
                except ValueError:
                    pass
                self.order.insert(0, key)
                return self.cache[key]
            return None

    async def set(self, key: Any, value: Any):
        async with self.lock:
            if key in self.cache:
                try:
                    self.order.remove(key)
                except ValueError:
                    pass
            self.cache[key] = value
            self.order.insert(0, key)
            if len(self.order) > self.maxsize:
                old = self.order.pop()
                self.cache.pop(old, None)

    async def clear(self):
        async with self.lock:
            self.cache.clear()
            self.order.clear()

# Декоратор
def async_lru_cache_decorator(cache: AsyncLRU):
    def decorator(fn):
        async def wrapper(*args, **kwargs):
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            val = await cache.get(key)
            if val is not None:
                return val
            res = await fn(*args, **kwargs)
            await cache.set(key, res)
            return res
        return wrapper
    return decorator