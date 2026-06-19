from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.schemas.serialization import clean_payload


@dataclass(slots=True)
class TableSlot:
    code: str
    name: str
    slot: str
    roomNo: str
    courseType: str
    online: bool
    isOptional: bool = False


@dataclass(slots=True)
class DaySchedule:
    day: int
    table: list[TableSlot | None]


@dataclass(slots=True)
class TimetableResult:
    regNumber: str = ""
    batch: str = ""
    schedule: list[DaySchedule] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return clean_payload(self)
