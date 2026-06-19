from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.schemas.serialization import clean_payload


@dataclass(slots=True)
class Day:
    date: str
    day: str
    event: str
    dayOrder: str


@dataclass(slots=True)
class CalendarMonth:
    month: str
    days: list[Day] = field(default_factory=list)


@dataclass(slots=True)
class CalendarResponse:
    error: bool = False
    message: str | None = None
    status: int = 0
    today: Day | None = None
    tomorrow: Day | None = None
    index: int = 0
    calendar: list[CalendarMonth] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return clean_payload(self)
