from __future__ import annotations

from collections.abc import Mapping

import httpx

from core.config import Settings, settings
from core.constants import BROWSER_HEADERS
from core.exceptions import ScraperResponseError


class AcademiaClient:
    def __init__(self, cookie: str = "", config: Settings = settings) -> None:
        self.cookie = cookie
        self.config = config
        self._client = httpx.Client(
            timeout=config.request_timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AcademiaClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get(
        self, url: str, *, headers: Mapping[str, str] | None = None
    ) -> httpx.Response:
        response = self._client.get(url, headers=self._headers(headers))
        self._raise_for_unexpected_status(response)
        return response

    def post(
        self,
        url: str,
        *,
        data: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        follow_redirects: bool = True,
    ) -> httpx.Response:
        response = self._client.post(
            url,
            data=data,
            headers=self._headers(headers),
            follow_redirects=follow_redirects,
        )
        self._raise_for_unexpected_status(response)
        return response

    def delete(
        self, url: str, *, headers: Mapping[str, str] | None = None
    ) -> httpx.Response:
        response = self._client.delete(url, headers=self._headers(headers))
        self._raise_for_unexpected_status(response)
        return response

    def fetch_academia_page(self, url: str) -> str:
        response = self.get(url, headers=BROWSER_HEADERS)
        if response.status_code != httpx.codes.OK:
            raise ScraperResponseError(f"server returned status {response.status_code}")
        return response.text

    def _headers(self, headers: Mapping[str, str] | None) -> dict[str, str]:
        merged = dict(headers or {})
        if self.cookie:
            merged.setdefault("Cookie", self.cookie)
        return merged

    @staticmethod
    def _raise_for_unexpected_status(response: httpx.Response) -> None:
        if response.status_code >= 500:
            raise ScraperResponseError(f"server returned status {response.status_code}")
