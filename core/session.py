from __future__ import annotations

from http.cookies import SimpleCookie


class CookieJar:
    def __init__(self) -> None:
        self._cookies: dict[str, str] = {}

    def update_from_response(self, set_cookie_headers: list[str]) -> None:
        for header in set_cookie_headers:
            cookie = SimpleCookie()
            cookie.load(header)
            for key, morsel in cookie.items():
                value = morsel.value
                if value and value not in {"delete", "null"}:
                    self._cookies[key] = value

    def header(self) -> str:
        return "; ".join(f"{key}={value}" for key, value in self._cookies.items())

    def __bool__(self) -> bool:
        return bool(self._cookies)
