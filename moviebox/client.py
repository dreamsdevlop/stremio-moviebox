import json
from typing import Any, Dict, Optional, Tuple

import httpx

from config import settings
from logger import get_logger
from moviebox.crypto import (
    build_signed_headers,
    generate_client_info_and_ua,
    random_spoofed_ip,
)

logger = get_logger("moviebox.client")

HOST_POOL = [
    "https://api6.aoneroom.com",
    "https://api5.aoneroom.com",
    "https://api4.aoneroom.com",
    "https://api4sg.aoneroom.com",
    "https://api3.aoneroom.com",
    "https://api6sg.aoneroom.com",
    "https://api.inprovider.com",
]
AUTH_TOKEN = None

class MovieBoxClient:
    def __init__(self):
        self.host_pool = HOST_POOL
        self.active_base = self.host_pool[0]
        self.client: httpx.AsyncClient | None = None
        self.runtime_token = AUTH_TOKEN
        self.user_agent, self.client_info = generate_client_info_and_ua()
        self.spoofed_ip = random_spoofed_ip()

    async def start(self):
        self.client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
        )
        if not self.runtime_token:
            await self._request("GET", "/wefeed-mobile-bff/tab-operating?page=1&tabId=0&version=")
        return self

    async def close(self):
        if self.client:
            await self.client.aclose()

    def _absorb_x_user(self, headers: httpx.Headers) -> None:
        x_user = headers.get("x-user", "")
        if x_user:
            try:
                payload = json.loads(x_user)
                token = payload.get("token")
                if token:
                    self.runtime_token = token
            except Exception:
                pass

    async def _request(self, method: str, path_and_query: str, body: str | None = None) -> tuple[str, httpx.Response]:
        last_exception = None
        
        for base in self.host_pool:
            url = f"{base}{path_and_query}"
            headers = build_signed_headers(
                method=method,
                url=url,
                body=body,
                auth_token=self.runtime_token,
                client_info=self.client_info,
                user_agent=self.user_agent,
                spoofed_ip=self.spoofed_ip
            )
            try:
                if method == "GET":
                    response = await self.client.get(url, headers=headers)
                else:
                    response = await self.client.post(url, headers=headers, content=body.encode() if body else b"")
                
                self._absorb_x_user(response.headers)
                
                if response.status_code not in {403, 406, 407, 429, 500, 502, 503, 504}:
                    self.active_base = base
                    return base, response
            except httpx.TransportError as exc:
                last_exception = exc
                
        raise RuntimeError(f"All hosts exhausted for {path_and_query}. Last error: {last_exception}")

    async def get(self, path: str) -> dict[str, Any]:
        _, response = await self._request("GET", path)
        return self._process_response(response)

    async def post(self, path: str, json_data: dict) -> dict[str, Any]:
        _, response = await self._request("POST", path, body=json.dumps(json_data))
        return self._process_response(response)
        
    def _process_response(self, response: httpx.Response) -> dict[str, Any]:
        data = response.json()
        if data.get("code", 1) == 0 and data.get("message") == "ok":
            return data.get("data", {})
        raise ValueError(f"API Error: {data}")
