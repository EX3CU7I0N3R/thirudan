from __future__ import annotations

import base64
import html
import random
import re
import string
import time
from typing import Any

REG_NUMBER_RE = re.compile(r"RA2\d{12}")
HEX_ESCAPE_RE = re.compile(r"\\x([0-9A-Fa-f]{2})")


def encode_token(value: str) -> str:
    hash_value = 2166136261
    for char in value:
        hash_value ^= ord(char)
        hash_value = (
            hash_value
            + (hash_value << 1)
            + (hash_value << 4)
            + (hash_value << 7)
            + (hash_value << 8)
            + (hash_value << 24)
        ) & 0xFFFFFFFF
    return f"{hash_value}{hash_value >> 1:x}{_base32_int(hash_value >> 2)}"


def decode_base64(value: str) -> str:
    return base64.b64decode(value).decode()


def convert_hex_to_html(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    decoded = HEX_ESCAPE_RE.sub(replace, value or "")
    return (
        decoded.replace(r"\-", "-")
        .replace(r"\/", "/")
        .replace(r"\'", "'")
        .replace(r"\\", "\\")
    )


def decode_html_entities(value: str) -> str:
    return html.unescape(value or "")


def parse_float(value: str) -> float:
    match = re.match(r"\s*([+-]?\d+(?:\.\d+)?)", value or "")
    return float(match.group(1)) if match else 0.0


def parse_int(value: str) -> int:
    match = re.match(r"\s*([+-]?\d+)", value or "")
    return int(match.group(1)) if match else 0


def find_reg_number(value: str) -> str:
    match = REG_NUMBER_RE.search(value or "")
    return match.group(0) if match else ""


def get_cookie(cookie_header: str, name: str) -> str:
    match = re.search(rf"{re.escape(name)}=([^;]+)", cookie_header or "")
    return match.group(1) if match else ""


def extract_calendar_cookies(cookie_header: str) -> str:
    iamadt = get_cookie(cookie_header, "_iamadt_client_10002227248")
    iambdt = get_cookie(cookie_header, "_iambdt_client_10002227248")
    return f"_iamadt_client_10002227248={iamadt}; _iambdt_client_10002227248={iambdt};"


def generate_id(length: int = 12) -> str:
    rng = random.SystemRandom()
    return "".join(rng.choice(string.digits) for _ in range(length))


def now_ms() -> int:
    return int(time.time() * 1000)


def dataclass_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    raise TypeError(f"{type(value).__name__} does not expose to_dict()")


def _base32_int(value: int) -> str:
    alphabet = "0123456789abcdefghijklmnopqrstuv"
    if value == 0:
        return "0"
    pieces: list[str] = []
    while value:
        value, remainder = divmod(value, 32)
        pieces.append(alphabet[remainder])
    return "".join(reversed(pieces))
