import os
import tomllib
from pathlib import Path
from dataclasses import dataclass

with open(Path(__file__).parent / "pyproject.toml", "rb") as f:
    _pyproject = tomllib.load(f)
    _version = _pyproject.get("project", {}).get("version", "1.0.0")

@dataclass
class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    VERSION: str = _version

settings = Settings()
