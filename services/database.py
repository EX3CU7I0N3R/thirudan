from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime
from typing import Any

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.config import Settings, settings
from core.exceptions import ConfigurationError
from core.schemas.calendar import CalendarMonth, Day
from core.utils import generate_id, now_ms
from scraper.parser import calendar_response_for_date, sort_calendar


class SnapshotStore:
    def __init__(self, config: Settings = settings) -> None:
        if not config.supabase_url or not config.supabase_key:
            raise ConfigurationError("SUPABASE_URL and SUPABASE_KEY are required")
        if not config.encryption_key:
            raise ConfigurationError("ENCRYPTION_KEY is required")

        self.base_url = config.supabase_url.rstrip("/")
        self.scrape_table = config.scrape_table
        self.calendar_table = config.calendar_table
        self.student_key_column = config.student_key_column
        self.session_key_column = config.session_key_column
        self.refreshed_at_column = config.refreshed_at_column
        self.schedule_note_column = config.schedule_note_column
        self.client = httpx.Client(
            headers={
                "apikey": config.supabase_key,
                "Authorization": f"Bearer {config.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            timeout=config.request_timeout,
        )
        self.key = hashlib.sha256(config.encryption_key.encode()).digest()

    def find_by_session_hash(self, session_hash: str) -> dict[str, Any] | None:
        response = self.client.get(
            f"{self.base_url}/rest/v1/{self.scrape_table}",
            params={self.session_key_column: f"eq.{session_hash}", "select": "*"},
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None

        row = rows[0]
        for key, value in list(row.items()):
            if not isinstance(value, str):
                continue
            if key == "timetable":
                row[key] = json.loads(value)
            elif key not in self._plain_columns():
                row[key] = json.loads(self._decrypt(value))
        return row

    def upsert_snapshot(self, payload: dict[str, Any]) -> None:
        record = self._to_storage_record(payload)
        record[self.refreshed_at_column] = now_ms()
        for key, value in list(record.items()):
            if key not in self._plain_columns():
                record[key] = self._encrypt(json.dumps(value, separators=(",", ":")))

        response = self.client.post(
            f"{self.base_url}/rest/v1/{self.scrape_table}",
            params={"on_conflict": self.student_key_column},
            headers={"Prefer": "resolution=merge-duplicates"},
            json=record,
        )
        response.raise_for_status()

    def get_schedule_note(self, session_hash: str) -> str:
        response = self.client.get(
            f"{self.base_url}/rest/v1/{self.scrape_table}",
            params={
                self.session_key_column: f"eq.{session_hash}",
                "select": self.schedule_note_column,
            },
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0].get(self.schedule_note_column) or "" if rows else ""

    def get_calendar(self) -> dict[str, Any] | None:
        response = self.client.get(
            f"{self.base_url}/rest/v1/{self.calendar_table}", params={"select": "*"}
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None

        month_map: dict[str, CalendarMonth] = {}
        for row in rows:
            month = month_map.setdefault(
                row["month"], CalendarMonth(month=row["month"], days=[])
            )
            month.days.append(
                Day(
                    date=row.get("date", ""),
                    day=row.get("day", ""),
                    event=row.get("event", ""),
                    dayOrder=row.get("order", ""),
                )
            )

        return calendar_response_for_date(
            sort_calendar(list(month_map.values())), datetime.now()
        ).to_dict()

    def store_calendar(self, calendar: list[dict[str, Any]]) -> None:
        rows = []
        for month in calendar:
            for day in month.get("days", []):
                rows.append(
                    {
                        "id": generate_id(),
                        "date": day.get("date", ""),
                        "month": month.get("month", ""),
                        "day": day.get("day", ""),
                        "order": day.get("dayOrder", ""),
                        "event": day.get("event", ""),
                        "created_at": now_ms(),
                    }
                )
        if rows:
            response = self.client.post(
                f"{self.base_url}/rest/v1/{self.calendar_table}", json=rows
            )
            response.raise_for_status()

    def _encrypt(self, value: str) -> str:
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        return base64.b64encode(
            nonce + aesgcm.encrypt(nonce, value.encode(), None)
        ).decode()

    def _decrypt(self, value: str) -> str:
        ciphertext = base64.b64decode(value)
        nonce, body = ciphertext[:12], ciphertext[12:]
        return AESGCM(self.key).decrypt(nonce, body, None).decode()

    def _plain_columns(self) -> set[str]:
        return {
            self.student_key_column,
            self.session_key_column,
            self.refreshed_at_column,
            self.schedule_note_column,
            "timetable",
        }

    def _to_storage_record(self, payload: dict[str, Any]) -> dict[str, Any]:
        record = dict(payload)
        if "regNumber" in record:
            record[self.student_key_column] = record.pop("regNumber")
        if "token" in record:
            record[self.session_key_column] = record.pop("token")
        if "scheduleNote" in record:
            record[self.schedule_note_column] = record.pop("scheduleNote")
        return record
