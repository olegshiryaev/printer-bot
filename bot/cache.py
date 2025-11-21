from functools import cache

# Просто импортируем и используем @cache — он полностью async-safe
# Если нужен TTL — раскомментируй блок ниже и установи aiocache

# from aiocache import cached, Cache
# from aiocache.serializers import JsonSerializer
#
# def cached_api(ttl: int = 300):
#     return cached(ttl=ttl, cache=Cache.MEMORY, serializer=JsonSerializer())