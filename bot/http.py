import logging
from httpx import AsyncClient, Limits, HTTPStatusError, RequestError

from .config import settings

logger = logging.getLogger(__name__)

client = AsyncClient(
    base_url=settings.API_BASE.rstrip("/"),
    timeout=12.0,
    limits=Limits(max_connections=100, max_keepalive_connections=20),
    # если хочешь ещё строже:
    # limits=Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=30),
)


async def api_get(url: str, params=None):
    try:
        r = await client.get(url, params=params or {})
        r.raise_for_status()
        return r.json()
    except HTTPStatusError as exc:
        logger.error(f"API error {exc.response.status_code} {url}")
        return {"items": [], "total": 0}
    except RequestError as exc:
        logger.error(f"Request failed {url}: {exc}")
        return {"items": [], "total": 0}
    except Exception as exc:
        logger.exception(f"Unexpected error {url}")
        return {"items": [], "total": 0}