from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.schemas.serialization import clean_payload


@dataclass(slots=True)
class Attendance:
    courseCode: str
    courseTitle: str
    category: str
    facultyName: str
    slot: str
    hoursConducted: str
    hoursAbsent: str
    attendancePercentage: str


@dataclass(slots=True)
class AttendanceResponse:
    regNumber: str = ""
    attendance: list[Attendance] = field(default_factory=list)
    status: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean_payload(self)


@dataclass(slots=True)
class MarksDetail:
    scored: str
    total: str


@dataclass(slots=True)
class TestPerformance:
    test: str
    marks: MarksDetail


@dataclass(slots=True)
class Mark:
    courseName: str
    courseCode: str
    courseType: str
    overall: MarksDetail
    testPerformance: list[TestPerformance]


@dataclass(slots=True)
class MarksResponse:
    regNumber: str = ""
    marks: list[Mark] = field(default_factory=list)
    status: int = 200
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean_payload(self)


@dataclass(slots=True)
class Course:
    code: str
    title: str
    credit: str
    category: str
    courseCategory: str
    type: str
    slotType: str
    faculty: str
    slot: str
    room: str
    academicYear: str


@dataclass(slots=True)
class CourseResponse:
    regNumber: str = ""
    courses: list[Course] = field(default_factory=list)
    status: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return clean_payload(self)


@dataclass(slots=True)
class User:
    name: str = ""
    mobile: str = ""
    program: str = ""
    semester: int = 0
    regNumber: str = ""
    batch: str = ""
    year: int = 0
    department: str = ""
    section: str = ""
    specialization: str = ""

    def to_dict(self) -> dict[str, Any]:
        return clean_payload(self, omit_empty=False)
