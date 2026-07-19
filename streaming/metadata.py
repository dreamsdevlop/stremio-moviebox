import httpx

from config import settings


async def resolve_imdb_id(type_: str, imdb_id: str) -> dict:
    url = f"https://v3-cinemeta.strem.io/meta/{type_}/{imdb_id}.json"
    try:
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json().get("meta", {})
    except Exception:
        pass
    return {}
