from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.schemas.academics import Course, CourseResponse
from core.schemas.timetable import DaySchedule, TableSlot, TimetableResult


@dataclass(frozen=True)
class SlotDay:
    day: int
    dayOrder: str
    slots: tuple[str, ...]


@dataclass(frozen=True)
class Batch:
    batch: str
    slots: tuple[SlotDay, ...]


BATCH_1 = Batch(
    "1",
    (
        SlotDay(1, "Day 1", ("A", "A", "F", "F", "G", "P6", "P7", "P8", "P9", "P10")),
        SlotDay(
            2, "Day 2", ("P11", "P12", "P13", "P14", "P15", "B", "B", "G", "G", "A")
        ),
        SlotDay(
            3, "Day 3", ("C", "C", "A", "D", "B", "P26", "P27", "P28", "P29", "P30")
        ),
        SlotDay(
            4, "Day 4", ("P31", "P32", "P33", "P34", "P35", "D", "D", "B", "E", "C")
        ),
        SlotDay(
            5, "Day 5", ("E", "E", "C", "F", "D", "P46", "P47", "P48", "P49", "P50")
        ),
    ),
)
BATCH_2 = Batch(
    "2",
    (
        SlotDay(1, "Day 1", ("P1", "P2", "P3", "P4", "P5", "A", "A", "F", "F", "G")),
        SlotDay(
            2, "Day 2", ("B", "B", "G", "G", "A", "P16", "P17", "P18", "P19", "P20")
        ),
        SlotDay(
            3, "Day 3", ("P21", "P22", "P23", "P24", "P25", "C", "C", "A", "D", "B")
        ),
        SlotDay(
            4, "Day 4", ("D", "D", "B", "E", "C", "P36", "P37", "P38", "P39", "P40")
        ),
        SlotDay(
            5, "Day 5", ("P41", "P42", "P43", "P44", "P45", "E", "E", "C", "F", "D")
        ),
    ),
)


class TimetableBuilder:
    def build(self, courses: CourseResponse, batch_number: int) -> TimetableResult:
        batch = {1: BATCH_1, 2: BATCH_2}.get(batch_number)
        if batch is None:
            return TimetableResult(regNumber="", batch=str(batch_number), schedule=[])
        return TimetableResult(
            regNumber=courses.regNumber,
            batch=batch.batch,
            schedule=self._map_slots(batch, courses.courses),
        )

    def _map_slots(self, batch: Batch, courses: list[Course]) -> list[DaySchedule]:
        slot_mapping: dict[str, list[TableSlot]] = {}

        for course in courses:
            for slot in self._slots_from_range(course.slot):
                is_online = "online" in course.room.lower()
                table_slot = TableSlot(
                    code=course.code,
                    name=course.title,
                    online=is_online,
                    courseType="Practical" if is_online else course.slotType,
                    roomNo=course.room,
                    slot=slot,
                )
                slot_mapping.setdefault(slot, []).append(table_slot)

        schedule: list[DaySchedule] = []
        for day in batch.slots:
            table: list[TableSlot | None] = []
            for slot in day.slots:
                matches = slot_mapping.get(slot)
                if not matches:
                    table.append(None)
                elif len(matches) == 1:
                    table.append(matches[0])
                else:
                    table.append(self._merge_slot(slot, matches))
            schedule.append(DaySchedule(day=day.day, table=table))
        return schedule

    @staticmethod
    def _slots_from_range(slot_range: str) -> list[str]:
        return slot_range.split("-") if "-" in slot_range else [slot_range]

    @staticmethod
    def _merge_slot(slot: str, matches: list[TableSlot]) -> TableSlot:
        return TableSlot(
            code="/".join(_unique(match.code for match in matches)),
            name="/".join(_unique(match.name for match in matches)),
            online=matches[0].online,
            courseType=matches[0].courseType,
            roomNo="/".join(_unique(match.roomNo for match in matches)),
            slot=slot,
        )


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:  # type: ignore[operator]
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
