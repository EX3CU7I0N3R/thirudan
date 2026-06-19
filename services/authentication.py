from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from core.config import Settings, settings
from core.constants import (
    ACTIVE_SESSIONS_URL,
    BASE_URL,
    CAPTCHA_URL,
    LOGOUT_URL,
    PORTAL_ID,
    SERVICE_NAME,
    SIGNIN_URL,
)
from core.schemas.session import CaptchaData, LoginResponse
from core.session import CookieJar
from scraper.client import AcademiaClient


class LoginService:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config

    def login(
        self,
        username: str,
        password: str,
        cdigest: str | None = None,
        captcha: str | None = None,
    ) -> LoginResponse:
        full_username = username if "@" in username else f"{username}@srmist.edu.in"
        with AcademiaClient(config=self.config) as client:
            return self._login_with_retry(
                client, full_username, password, cdigest, captcha, 0, CookieJar()
            )

    def logout(self, cookie: str) -> dict[str, Any]:
        with AcademiaClient(cookie=cookie, config=self.config) as client:
            response = client.get(LOGOUT_URL, headers={"User-Agent": "Mozilla/5.0"})
        return {
            "status": response.status_code,
            "success": response.status_code in {200, 302},
        }

    def cleanup(self, cookie: str) -> int:
        with AcademiaClient(cookie=cookie, config=self.config) as client:
            return client.delete(ACTIVE_SESSIONS_URL).status_code

    def _login_with_retry(
        self,
        client: AcademiaClient,
        username: str,
        password: str,
        cdigest: str | None,
        captcha: str | None,
        retry_count: int,
        jar: CookieJar,
    ) -> LoginResponse:
        if retry_count > 2:
            return LoginResponse(
                False,
                status=401,
                message="Too many retries after concurrent session termination",
            )

        form = {
            "username": username,
            "password": password,
            "client_portal": "true",
            "portal": PORTAL_ID,
            "servicename": SERVICE_NAME,
            "serviceurl": f"{BASE_URL}/",
            "is_ajax": "true",
            "grant_type": "password",
            "service_language": "en",
        }
        if cdigest:
            form["cdigest"] = cdigest
        if captcha:
            form["captcha"] = captcha

        response = client.post(
            SIGNIN_URL,
            data=form,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0",
                "Origin": BASE_URL,
                "Referer": f"{BASE_URL}/",
            },
            follow_redirects=False,
        )
        jar.update_from_response(response.headers.get_list("set-cookie"))

        body = response.text
        lowered = body.lower()
        if ("concurrent" in lowered or "terminate" in lowered) and self._force_logout(
            client, body, jar
        ):
            return self._login_with_retry(
                client, username, password, cdigest, captcha, retry_count + 1, jar
            )

        try:
            payload = response.json()
        except ValueError:
            return LoginResponse(
                False,
                status=response.status_code,
                message="Unexpected response from server",
            )

        error = payload.get("error")
        if isinstance(error, dict):
            return LoginResponse(False, status=401, message=error.get("msg", ""))

        if payload.get("status") == "fail" and payload.get("code") in {
            "HIP_REQUIRED",
            "HIP_FAILED",
        }:
            captcha_data = None
            if payload.get("cdigest"):
                captcha_data = CaptchaData(
                    image=CAPTCHA_URL.format(cdigest=payload["cdigest"]),
                    cdigest=payload["cdigest"],
                )
            return LoginResponse(
                False, status=401, message=payload.get("message"), captcha=captcha_data
            )

        inner = payload.get("data")
        if not isinstance(inner, dict):
            return LoginResponse(
                False,
                status=401,
                message=payload.get("message", ""),
                errors=["Invalid credentials"],
            )

        access_token = inner.get("access_token")
        redirect_url = inner.get("oauthorize_uri")
        if not access_token or not redirect_url:
            return LoginResponse(
                False, status=401, message="Missing tokens in response"
            )

        auth_response = client.get(
            f"{redirect_url}&access_token={access_token}",
            headers={"Cookie": jar.header()},
        )
        jar.update_from_response(auth_response.headers.get_list("set-cookie"))
        cookie_header = jar.header()

        if "JSESSIONID" not in cookie_header:
            return LoginResponse(
                False, status=401, message="Session failed: JSESSIONID not established"
            )

        return LoginResponse(
            True,
            session={"success": True},
            cookies=cookie_header,
            status=200,
            message="Success",
        )

    def _force_logout(self, client: AcademiaClient, html: str, jar: CookieJar) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        terminate_form = next(
            (
                form
                for form in soup.find_all("form")
                if "terminate" in form.get_text(" ", strip=True).lower()
            ),
            None,
        )
        if terminate_form is None:
            return False

        action = terminate_form.get("action") or ""
        if not action.startswith("http"):
            action = f"{BASE_URL}{action}"

        payload = {
            field.get("name"): field.get("value", "")
            for field in terminate_form.find_all("input")
            if field.get("name")
        }
        response = client.post(
            action,
            data=payload,
            headers={
                "Cookie": jar.header(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        jar.update_from_response(response.headers.get_list("set-cookie"))
        return response.status_code == 200
