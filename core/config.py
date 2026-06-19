from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


@dataclass(frozen=True)
class Settings:
    port: int = 8080
    frontend_url: str | None = None
    allow_file_origin: bool = False
    academia_base_url: str = "https://academia.srmist.edu.in"
    portal_id: str = "10002227248"
    service_name: str = "ZohoCreator"
    attendance_page_name: str = "My_Attendance"
    course_page_name: str = "My_Time_Table_2023_24"
    calendar_page_name: str = "Academic_Planner_2025_26_EVEN"
    supabase_url: str | None = None
    supabase_key: str | None = None
    encryption_key: str | None = None
    scrape_table: str = "scrape_cache"
    calendar_table: str = "academic_calendar"
    student_key_column: str = "student_id"
    session_key_column: str = "session_hash"
    refreshed_at_column: str = "refreshed_at"
    schedule_note_column: str = "schedule_note"
    request_timeout: float = 30.0
    cache_ttl_seconds: int = 120
    cache_max_entries: int = 512
    max_request_body_bytes: int = 16_384

    @classmethod
    def from_env(cls) -> "Settings":
        if load_dotenv is not None:
            load_dotenv()

        return cls(
            port=int(os.getenv("PORT", "8080")),
            frontend_url=os.getenv("URL"),
            allow_file_origin=os.getenv("ALLOW_FILE_ORIGIN", "false").lower()
            in {"1", "true", "yes"},
            academia_base_url=os.getenv(
                "ACADEMIA_BASE_URL", "https://academia.srmist.edu.in"
            ).rstrip("/"),
            portal_id=os.getenv("ACADEMIA_PORTAL_ID", "10002227248"),
            service_name=os.getenv("ACADEMIA_SERVICE_NAME", "ZohoCreator"),
            attendance_page_name=os.getenv("ATTENDANCE_PAGE_NAME", "My_Attendance"),
            course_page_name=os.getenv("COURSE_PAGE_NAME", "My_Time_Table_2023_24"),
            calendar_page_name=os.getenv(
                "CALENDAR_PAGE_NAME", "Academic_Planner_2025_26_EVEN"
            ),
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            encryption_key=os.getenv("ENCRYPTION_KEY"),
            scrape_table=os.getenv("SCRAPE_TABLE", "scrape_cache"),
            calendar_table=os.getenv("CALENDAR_TABLE", "academic_calendar"),
            student_key_column=os.getenv("STUDENT_KEY_COLUMN", "student_id"),
            session_key_column=os.getenv("SESSION_KEY_COLUMN", "session_hash"),
            refreshed_at_column=os.getenv("REFRESHED_AT_COLUMN", "refreshed_at"),
            schedule_note_column=os.getenv("SCHEDULE_NOTE_COLUMN", "schedule_note"),
            request_timeout=float(os.getenv("REQUEST_TIMEOUT", "30")),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "120")),
            cache_max_entries=int(os.getenv("CACHE_MAX_ENTRIES", "512")),
            max_request_body_bytes=int(os.getenv("MAX_REQUEST_BODY_BYTES", "16384")),
        )


settings = Settings.from_env()
