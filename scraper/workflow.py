from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from core.constants import ATTENDANCE_PAGE, CALENDAR_PAGE, COURSE_PAGE
from core.markup import extract_sanitized_html
from core.schemas.academics import (
    AttendanceResponse,
    CourseResponse,
    MarksResponse,
    User,
)
from core.schemas.calendar import CalendarResponse
from core.schemas.timetable import TimetableResult
from core.utils import dataclass_dict
from scraper.client import AcademiaClient
from scraper.parser import AcademiaParser
from scraper.timetable import TimetableBuilder


class AcademiaScraper:
    def __init__(self, cookie: str) -> None:
        self.cookie = cookie
        self.parser = AcademiaParser()
        self.timetable_builder = TimetableBuilder()

    def attendance(self) -> AttendanceResponse:
        try:
            return self.parser.parse_attendance(self._attendance_html())
        except Exception as exc:
            return AttendanceResponse(status=500, error=str(exc), attendance=[])

    def marks(self) -> MarksResponse:
        try:
            return self.parser.parse_marks(self._attendance_html())
        except Exception as exc:
            return MarksResponse(status=500, error=str(exc), marks=[])

    def courses(self) -> CourseResponse:
        try:
            return self.parser.parse_courses(self._course_html())
        except Exception as exc:
            return CourseResponse(status=500, error=str(exc), courses=[])

    def user(self) -> User:
        return self.parser.parse_user(self._course_html())

    def calendar(self) -> CalendarResponse:
        with AcademiaClient(cookie=self._calendar_cookie()) as client:
            response = client.get(
                CALENDAR_PAGE,
                headers={
                    "accept": "*/*",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Referer": "https://academia.srmist.edu.in/",
                    "Cache-Control": "public, max-age=3600, stale-while-revalidate=7200",
                },
            )
        if response.status_code != 200:
            return CalendarResponse(
                error=True,
                message=f"HTTP error: {response.status_code}",
                status=response.status_code,
                calendar=[],
            )
        return self.parser.parse_calendar(response.text)

    def timetable(self) -> TimetableResult:
        user = self.user()
        try:
            batch = int(user.batch or "1")
        except ValueError:
            return TimetableResult(regNumber="", batch=user.batch, schedule=[])
        return self.timetable_builder.build(self.courses(), batch)

    def all_data(self) -> dict[str, Any]:
        jobs = {
            "user": self.user,
            "attendance": self.attendance,
            "marks": self.marks,
            "courses": self.courses,
            "timetable": self.timetable,
        }
        payload: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(func): key for key, func in jobs.items()}
            for future in as_completed(futures):
                key = futures[future]
                value = future.result()
                payload[key] = dataclass_dict(value)

        user = payload.get("user")
        if isinstance(user, dict) and user.get("regNumber"):
            payload["regNumber"] = user["regNumber"]
        return payload

    def _attendance_html(self) -> str:
        with AcademiaClient(cookie=self.cookie) as client:
            response_text = client.fetch_academia_page(ATTENDANCE_PAGE)
        return extract_sanitized_html(response_text, "attendance")

    def _course_html(self) -> str:
        with AcademiaClient(cookie=self.cookie) as client:
            response_text = client.fetch_academia_page(COURSE_PAGE)
        return extract_sanitized_html(response_text, "course")

    def _calendar_cookie(self) -> str:
        from core.utils import extract_calendar_cookies

        return f"ZCNEWUIPUBLICPORTAL=true; cli_rgn=IN; {extract_calendar_cookies(self.cookie)}"
