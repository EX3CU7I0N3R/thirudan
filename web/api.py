from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from core.cache import ResponseCache
from core.config import settings
from core.exceptions import ConfigurationError, ParseError
from core.middleware import RequestSizeLimitMiddleware, SecurityHeadersMiddleware
from core.rate_limit import SlidingWindowRateLimiter
from core.utils import encode_token
from scraper.workflow import AcademiaScraper
from services.authentication import LoginService
from services.database import SnapshotStore

app = FastAPI(title="Thirudan", version="1.0")
cache = ResponseCache(settings.cache_ttl_seconds, settings.cache_max_entries)
executor = ThreadPoolExecutor(max_workers=4)

allowed_origins = [
    "http://localhost:243",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
if settings.allow_file_origin:
    allowed_origins.append("null")
if settings.frontend_url:
    allowed_origins.extend(
        origin.strip() for origin in settings.frontend_url.split(",") if origin.strip()
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Origin", "Content-Type", "Accept", "X-CSRF-Token"],
    expose_headers=["Content-Length"],
    allow_credentials=True,
)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(SlidingWindowRateLimiter)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RequestSizeLimitMiddleware, max_body_bytes=settings.max_request_body_bytes
)


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(exc.detail, status_code=exc.status_code)


@app.exception_handler(Exception)
async def handle_exception(_: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, ParseError) and "invalid response format" in str(exc):
        return JSONResponse(
            {
                "tokenInvalid": True,
                "error": "Session expired or invalid",
                "status": 401,
            },
            status_code=401,
        )
    return JSONResponse(
        {"error": "Internal server error", "status": 500}, status_code=500
    )


@app.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello, World!"}


@app.post("/login")
async def login(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(400, {"error": "Invalid JSON body"})
    username = payload.get("account", "")
    password = payload.get("password", "")
    if not username or not password:
        raise HTTPException(400, {"error": "Missing account or password"})
    response = LoginService().login(
        username, password, payload.get("cdigest"), payload.get("captcha")
    )
    return response.to_dict()


@app.delete("/logout")
def logout(
    x_csrf_token: str = Header(default="", alias="X-CSRF-Token"),
) -> dict[str, Any]:
    _require_session_cookie(x_csrf_token)
    return LoginService().logout(x_csrf_token)


@app.get("/attendance")
def attendance(
    x_csrf_token: str = Header(default="", alias="X-CSRF-Token"),
) -> dict[str, Any]:
    _require_session_cookie(x_csrf_token)
    return _cached(
        "attendance",
        x_csrf_token,
        lambda: AcademiaScraper(x_csrf_token).attendance().to_dict(),
    )


@app.get("/marks")
def marks(
    x_csrf_token: str = Header(default="", alias="X-CSRF-Token"),
) -> dict[str, Any]:
    _require_session_cookie(x_csrf_token)
    return _cached(
        "marks", x_csrf_token, lambda: AcademiaScraper(x_csrf_token).marks().to_dict()
    )


@app.get("/courses")
def courses(
    x_csrf_token: str = Header(default="", alias="X-CSRF-Token"),
) -> dict[str, Any]:
    _require_session_cookie(x_csrf_token)
    return _cached(
        "courses",
        x_csrf_token,
        lambda: AcademiaScraper(x_csrf_token).courses().to_dict(),
    )


@app.get("/user")
def user(
    x_csrf_token: str = Header(default="", alias="X-CSRF-Token"),
) -> dict[str, Any]:
    _require_session_cookie(x_csrf_token)
    return _cached(
        "user", x_csrf_token, lambda: AcademiaScraper(x_csrf_token).user().to_dict()
    )


@app.get("/calendar")
def calendar(
    x_csrf_token: str = Header(default="", alias="X-CSRF-Token"),
) -> dict[str, Any]:
    _require_session_cookie(x_csrf_token)

    def fetch() -> dict[str, Any]:
        store = _store_or_none()
        if store:
            cached_calendar = store.get_calendar()
            if cached_calendar and cached_calendar.get("calendar"):
                return cached_calendar
        response = AcademiaScraper(x_csrf_token).calendar().to_dict()
        if store and response.get("calendar"):
            executor.submit(store.store_calendar, response["calendar"])
        return response

    return _cached("calendar", x_csrf_token, fetch)


@app.get("/timetable")
def timetable(
    x_csrf_token: str = Header(default="", alias="X-CSRF-Token"),
) -> dict[str, Any]:
    _require_session_cookie(x_csrf_token)
    return _cached(
        "timetable",
        x_csrf_token,
        lambda: AcademiaScraper(x_csrf_token).timetable().to_dict(),
    )


@app.get("/get")
def get_all(
    x_csrf_token: str = Header(default="", alias="X-CSRF-Token"),
) -> dict[str, Any]:
    _require_session_cookie(x_csrf_token)
    encoded_token = encode_token(x_csrf_token)
    store = _store_or_none()

    if store:
        cached_data = store.find_by_session_hash(encoded_token)
        if (
            cached_data
            and cached_data.get("timetable") is not None
            and cached_data.get("attendance") is not None
            and cached_data.get("marks") is not None
        ):
            schedule_note = store.get_schedule_note(encoded_token)
            if schedule_note:
                cached_data["scheduleNote"] = schedule_note
            executor.submit(_refresh_all, x_csrf_token, encoded_token, store)
            return cached_data

    data = AcademiaScraper(x_csrf_token).all_data()
    data["token"] = encoded_token
    if store:
        schedule_note = store.get_schedule_note(encoded_token)
        if schedule_note:
            data["scheduleNote"] = schedule_note
        executor.submit(store.upsert_snapshot, dict(data))
    return data


def _cached(name: str, token: str, factory: Any) -> dict[str, Any]:
    key = f"/{name}_{encode_token(token)}"
    cached_value = cache.get(key)
    if cached_value is not None:
        return cached_value
    return cache.set(key, factory())


def _refresh_all(token: str, encoded_token: str, store: SnapshotStore) -> None:
    data = AcademiaScraper(token).all_data()
    data["token"] = encoded_token
    store.upsert_snapshot(data)


def _store_or_none() -> SnapshotStore | None:
    try:
        return SnapshotStore()
    except ConfigurationError:
        return None


def _require_session_cookie(token: str) -> None:
    if not token:
        raise HTTPException(401, {"error": "Missing X-CSRF-Token header"})
