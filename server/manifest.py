import json

from pydantic import BaseModel

from config import settings


class Manifest(BaseModel):
    id: str
    version: str
    name: str
    description: str
    resources: list[str]
    types: list[str]
    catalogs: list
    idPrefixes: list[str]
    logo: str | None = None

def get_manifest() -> Manifest:
    return Manifest(
        id="com.moviebox.addon",
        version=settings.VERSION,
        name="MovieBox",
        description="Stream movies and TV series with multiple qualities, audio languages, and subtitles.",
        resources=["stream"],
        types=["movie", "series"],
        catalogs=[],
        idPrefixes=["tt"],
    )
