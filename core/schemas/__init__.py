from core.schemas.academics import (
    Attendance,
    AttendanceResponse,
    Course,
    CourseResponse,
    Mark,
    MarksDetail,
    MarksResponse,
    TestPerformance,
    User,
)
from core.schemas.calendar import CalendarMonth, CalendarResponse, Day
from core.schemas.session import CaptchaData, LoginResponse
from core.schemas.timetable import DaySchedule, TableSlot, TimetableResult

__all__ = [
    "Attendance",
    "AttendanceResponse",
    "CalendarMonth",
    "CalendarResponse",
    "CaptchaData",
    "Course",
    "CourseResponse",
    "Day",
    "DaySchedule",
    "LoginResponse",
    "Mark",
    "MarksDetail",
    "MarksResponse",
    "TableSlot",
    "TestPerformance",
    "TimetableResult",
    "User",
]
