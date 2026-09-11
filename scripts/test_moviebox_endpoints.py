#!/usr/bin/env python3
"""Test authorized MovieBox API preview endpoints.

Usage:
  export MOVIEBOX_API_KEY='your-rotated-key'
  python scripts/test_moviebox_endpoints.py --subject-id 123456

The key is read only from the environment and is never printed. Use this only
with an API subscription and content source you are authorized to access.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class Settings:
    base_url: str
    api_key: str
    api_host: str
    timeout: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test MovieBox preview endpoints")
    parser.add_argument("--subject-id", required=True, help="MovieBox subject ID")
    parser.add_argument(
        "--base-url",
        default=os.getenv("MOVIEBOX_API_BASE_URL", "https://moviebox-api.p.rapidapi.com"),
        help="Authorized API base URL",
    )
    parser.add_argument(
        "--api-host",
        default=os.getenv("MOVIEBOX_API_HOST", "moviebox-api.p.rapidapi.com"),
        help="RapidAPI host header value",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional key override; environment variable is safer",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--show-json", action="store_true", help="Print sanitized response JSON")
    return parser.parse_args()


def settings_from(args: argparse.Namespace) -> Settings:
    key = args.api_key or os.getenv("MOVIEBOX_API_KEY", "")
    if not key:
        raise SystemExit(
            "Missing MOVIEBOX_API_KEY. Set a newly rotated authorized key in the environment."
        )
    return Settings(
        base_url=args.base_url.rstrip("/"),
        api_key=key,
        api_host=args.api_host,
        timeout=args.timeout,
    )


def sanitize(value: Any, depth: int = 0) -> Any:
    """Keep diagnostics useful without printing tokens or huge media payloads."""
    if depth > 4:
        return "<nested value omitted>"
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(token in key_text for token in ("key", "token", "authorization", "cookie", "sign")):
                output[key] = "<redacted>"
            elif key_text in {"resourceLink", "url", "playUrl"} and isinstance(item, str):
                output[key] = item.split("?")[0] + ("?..." if "?" in item else "")
            else:
                output[key] = sanitize(item, depth + 1)
        return output
    if isinstance(value, list):
        return [sanitize(item, depth + 1) for item in value[:20]]
    return value


def summarize(path: str, status: int, body: Any, elapsed: float) -> None:
    if isinstance(body, dict):
        keys = ", ".join(str(key) for key in list(body)[:12]) or "no top-level keys"
    else:
        keys = type(body).__name__
    state = "PASS" if 200 <= status < 300 else "FAIL"
    print(f"[{state}] {path} -> HTTP {status} in {elapsed:.2f}s; {keys}")


def call(client: httpx.Client, settings: Settings, path: str) -> tuple[int, Any, float]:
    started = time.perf_counter()
    response = client.get(
        f"{settings.base_url}{path}",
        headers={
            "x-rapidapi-host": settings.api_host,
            "x-rapidapi-key": settings.api_key,
            "Accept": "application/json",
        },
    )
    elapsed = time.perf_counter() - started
    try:
        body = response.json()
    except ValueError:
        body = response.text[:500]
    return response.status_code, body, elapsed


def main() -> int:
    args = parse_args()
    settings = settings_from(args)
    subject_id = args.subject_id.strip()
    if not subject_id or "/" in subject_id:
        print("Invalid subject ID.", file=sys.stderr)
        return 2

    paths = [
        f"/preview/{subject_id}",
        f"/preview/{subject_id}/episode-info",
    ]
    failures = 0
    with httpx.Client(timeout=settings.timeout, follow_redirects=True) as client:
        for path in paths:
            try:
                status, body, elapsed = call(client, settings, path)
            except httpx.HTTPError as exc:
                print(f"[FAIL] {path} -> request error: {exc}")
                failures += 1
                continue
            summarize(path, status, body, elapsed)
            if args.show_json:
                print(json.dumps(sanitize(body), indent=2, ensure_ascii=False)[:12000])
            if not 200 <= status < 300:
                failures += 1

    if failures:
        print(f"\n{failures} endpoint check(s) failed.")
        return 1
    print("\nAll endpoint checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
