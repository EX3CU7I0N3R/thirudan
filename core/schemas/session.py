from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.schemas.serialization import clean_payload


@dataclass(slots=True)
class CaptchaData:
    image: str
    cdigest: str


@dataclass(slots=True)
class LoginResponse:
    authenticated: bool
    session: dict[str, Any] = field(default_factory=dict)
    lookup: Any = None
    cookies: str = ""
    status: int = 200
    message: Any = None
    errors: list[str] = field(default_factory=list)
    captcha: CaptchaData | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean_payload(self, omit_none=True)
