import base64
import hashlib
import hmac
import os
import random
import time
import uuid
from urllib.parse import parse_qs, urlparse, urlsplit

SECRET_KEY_DEFAULT: str = os.getenv("MOVIEBOX_SECRET_KEY_DEFAULT", "76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O").strip()
SECRET_KEY_ALT: str = os.getenv("MOVIEBOX_SECRET_KEY_ALT", "Xqn2nnO41/L92o1iuXhSLHTbXvY4Z5ZZ62m8mSLA").strip()
SIGNATURE_BODY_MAX_BYTES: int = 102_400
AUTH_FREE_PATHS = set()

def md5_hex(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def b64_decode(value: str) -> bytes:
    padding = (4 - len(value) % 4) % 4
    return base64.b64decode(value + "=" * padding)

def b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode()

def generate_x_client_token(timestamp_ms: int) -> str:
    ts = str(timestamp_ms)
    reversed_ts = ts[::-1]
    hash_val = md5_hex(reversed_ts.encode())
    return f"{ts},{hash_val}"

def _sorted_query_string(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    if not qs:
        return ""
    parts = []
    for key in sorted(qs.keys()):
        for value in qs[key]:
            parts.append(f"{key}={value}")
    return "&".join(parts)

def build_canonical_string(method: str, accept: str, content_type: str, url: str, body: str | None, timestamp_ms: int) -> str:
    parsed = urlparse(url)
    path = parsed.path or ""
    query = _sorted_query_string(url)
    canonical_url = f"{path}?{query}" if query else path

    body_bytes = body.encode("utf-8") if body is not None else None
    if body_bytes is not None:
        truncated = body_bytes[:SIGNATURE_BODY_MAX_BYTES]
        body_hash = md5_hex(truncated)
        body_length = str(len(body_bytes))
    else:
        body_hash = ""
        body_length = ""

    return (
        f"{method.upper()}\n"
        f"{accept or ''}\n"
        f"{content_type or ''}\n"
        f"{body_length}\n"
        f"{timestamp_ms}\n"
        f"{body_hash}\n"
        f"{canonical_url}"
    )

def generate_x_tr_signature(method: str, accept: str, content_type: str, url: str, body: str | None, timestamp_ms: int, use_alt_key: bool = False) -> str:
    canonical = build_canonical_string(method, accept, content_type, url, body, timestamp_ms)
    secret_b64 = SECRET_KEY_ALT if use_alt_key else SECRET_KEY_DEFAULT
    secret_bytes = b64_decode(secret_b64)
    mac = hmac.new(secret_bytes, canonical.encode("utf-8"), hashlib.md5)
    sig_b64 = b64_encode(mac.digest())
    return f"{timestamp_ms}|2|{sig_b64}"

def generate_client_info_and_ua() -> tuple[str, str]:
    android_versions = [
        ("9", "PQ3A.190605.03081104"),
        ("10", "QP1A.191005.007.A3"),
        ("11", "RP1A.200720.011"),
        ("12", "S1B.220414.015"),
        ("13", "TQ2A.230405.003"),
    ]
    redmi_devices = [
        ("23078RKD5C", "Redmi"),
        ("2201117TY", "Redmi"),
        ("2201117TG", "Redmi"),
        ("22101316G", "Redmi"),
        ("21121210G", "Redmi"),
        ("M2012K11AG", "Redmi"),
        ("M2007J20CG", "Redmi"),
    ]
    version_codes = [50020042, 50020043, 50020044, 50020045, 50020046]
    network_types = ["NETWORK_WIFI", "NETWORK_MOBILE"]
    timezones = [
        "Asia/Kolkata",
        "Asia/Shanghai",
        "Asia/Tokyo",
        "America/New_York",
        "Europe/London",
    ]

    android = random.choice(android_versions)
    device = random.choice(redmi_devices)
    version_code = random.choice(version_codes)
    network = random.choice(network_types)
    timezone = random.choice(timezones)
    gaid = str(uuid.uuid4())
    device_id = "".join(random.choice("0123456789abcdef") for _ in range(32))

    user_agent = f"com.community.oneroom/{version_code} (Linux; U; Android {android[0]}; en_US; {device[1]}; Build/{android[1]}; Cronet/135.0.7012.3)"
    client_info = f'{{"package_name":"com.community.oneroom","version_name":"3.0.03.0529.03","version_code":{version_code},"os":"android","os_version":"{android[0]}","install_ch":"ps","device_id":"{device_id}","install_store":"ps","gaid":"{gaid}","brand":"{device[1]}","model":"{device[0]}","system_language":"en","net":"{network}","region":"US","timezone":"{timezone}","sp_code":"40401","X-Play-Mode":"2"}}'

    return user_agent, client_info

def random_spoofed_ip() -> str:
    host = random.randint(1, 254)
    return f"103.241.224.{host}"

def build_signed_headers(
    method: str,
    url: str,
    auth_token: str | None,
    client_info: str,
    user_agent: str,
    spoofed_ip: str,
    body: str | None = None,
    accept: str = "application/json",
    content_type: str = "application/json",
    include_play_mode: bool = False,
) -> dict[str, str]:
    ts = int(time.time() * 1000)
    headers = {
        "User-Agent": user_agent,
        "Accept": accept,
        "Content-Type": content_type,
        "Connection": "keep-alive",
        "X-Client-Token": generate_x_client_token(ts),
        "x-tr-signature": generate_x_tr_signature(method, accept, content_type, url, body, ts),
        "X-Client-Info": client_info,
        "X-Client-Status": "0",
        "X-Forwarded-For": spoofed_ip,
    }
    
    if auth_token:
        url_component = urlsplit(url)
        if url_component.path not in AUTH_FREE_PATHS:
            headers["Authorization"] = f"Bearer {auth_token}"

    if include_play_mode:
        headers["X-Play-Mode"] = "2"
        
    return headers
