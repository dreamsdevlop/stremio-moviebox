import asyncio
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from logger import logger
from moviebox.client import MovieBoxClient
from moviebox.parser import MovieBoxParser
from server.routes import router as main_router

ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="MovieBox Clone", version=settings.VERSION)
app.mount("/assets", StaticFiles(directory=str(ROOT / "assets")), name="assets")
app.mount("/web", StaticFiles(directory=str(ROOT / "web")), name="web")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(main_router)

_CACHE: dict[str, tuple[float, object]] = {}
_CACHE_TTL = 90
_CACHE_LOCK = asyncio.Lock()

async def _cached(key: str, loader):
    now = time.monotonic()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < _CACHE_TTL:
        return hit[1]
    async with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if hit and time.monotonic() - hit[0] < _CACHE_TTL:
            return hit[1]
        value = await loader()
        _CACHE[key] = (time.monotonic(), value)
        return value


def _poster(item: dict) -> str | None:
    for key in ("cover", "coverUrl", "poster", "posterUrl", "image", "thumbnail"):
        value = item.get(key)
        if isinstance(value, dict):
            value = value.get("url") or value.get("resourceLink")
        if value:
            return str(value)
    return None


@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(str(ROOT / "web" / "index.html"))


@app.get("/api/search")
async def api_search(q: str = Query(min_length=1, max_length=120), page: int = Query(1, ge=1, le=100)):
    key = f"search:{q.strip().lower()}:{page}"
    async def load():
        client = MovieBoxClient()
        await client.start()
        try:
            parser = MovieBoxParser(client)
            output, seen = [], set()
            requests = [asyncio.wait_for(parser.search(q, is_movie=kind, page=page, per_page=20), 8) for kind in (True, False)]
            results = await asyncio.gather(*requests, return_exceptions=True)
            for is_movie, result in zip((True, False), results):
                if isinstance(result, Exception):
                    logger.warning("MovieBox search failed for %s: %s", q, result)
                    continue
                for item in result.items:
                    if str(item.subject_id) in seen:
                        continue
                    seen.add(str(item.subject_id))
                    raw = item.model_dump(by_alias=True)
                    output.append({"id": str(item.subject_id), "title": item.title, "year": item.year, "type": "movie" if is_movie else "series", "poster": _poster(raw), "corner": item.corner})
            return {"items": output, "page": page, "has_more": len(output) >= 10}
        finally:
            await client.close()
    try:
        return await _cached(key, load)
    except Exception as exc:
        logger.error("Search failed after host fallback: %s", exc)
        raise HTTPException(status_code=502, detail="MovieBox is temporarily unavailable. Please retry shortly.") from exc


@app.get("/api/catalog")
async def api_catalog(page: int = Query(1, ge=1, le=20)):
    """Return all authorized MovieBox home rows with poster and genre metadata."""
    client = MovieBoxClient()
    await client.start()
    try:
        data = await client.get(f"/wefeed-mobile-bff/tab-operating?page={page}&tabId=0&version=")
        rows = []
        for row in data.get("items", []):
            subjects = []
            for raw in row.get("subjects") or []:
                if not raw.get("subjectId") or not raw.get("title"):
                    continue
                cover = raw.get("cover") or {}
                subjects.append({
                    "id": str(raw["subjectId"]),
                    "title": raw.get("title", ""),
                    "year": str(raw.get("releaseDate", ""))[:4],
                    "type": "series" if raw.get("subjectType") == 2 else "movie",
                    "genre": raw.get("genre", ""),
                    "poster": cover.get("url") or (raw.get("image") or {}).get("url"),
                })
            if subjects:
                rows.append({"title": row.get("title") or "MovieBox", "items": subjects})
        return {"rows": rows, "page": page}
    finally:
        await client.close()


@app.get("/api/streams/{media_type}/{subject_id}")
async def api_streams(
    media_type: str,
    subject_id: str,
    season: int = Query(1, ge=1),
    episode: int = Query(1, ge=1),
):
    if media_type not in {"movie", "series"}:
        raise HTTPException(status_code=404, detail="Unsupported media type")
    client = MovieBoxClient()
    await client.start()
    try:
        parser = MovieBoxParser(client)
        is_movie = media_type == "movie"
        resolutions = [2160, 1080, 720, 480, 0] if is_movie else [2160, 1080, 720, 480, 0]
        links = []
        for resolution in resolutions:
            try:
                result = await parser.get_download_links(
                    subject_id=subject_id,
                    resolution=resolution,
                    is_movie=is_movie,
                    season=season,
                    episode=episode,
                )
                links.extend(result.file_list)
                if is_movie and links:
                    break
            except Exception as exc:
                logger.info("Resource lookup failed at %s: %s", resolution, exc)
        streams = []
        seen = set()
        for link in links:
            if not is_movie and (link.se != season or link.ep != episode):
                continue
            url = str(link.url)
            if url in seen:
                continue
            seen.add(url)
            quality = "4K" if link.resolution >= 2160 else f"{link.resolution}p"
            streams.append({
                "url": url,
                "title": f"{quality} · {link.size / (1024 ** 3):.2f} GB" if link.size else quality,
                "resolution": link.resolution,
                "filename": f"stream.{url.split('?')[0].rsplit('.', 1)[-1]}" if "." in url else "stream.mp4",
            })
        return {"streams": streams}
    finally:
        await client.close()


@app.get("/logo.png")
async def get_logo():
    return FileResponse(str(ROOT / "assets" / "logo.png"), media_type="image/png")


@app.get("/status")
async def status_check():
    return {
        "status": "operational",
        "provider": "MovieBox authorized backend",
        "cache_entries": len(_CACHE),
        "cache_ttl_seconds": _CACHE_TTL,
        "credentials_exposed_to_browser": False,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
