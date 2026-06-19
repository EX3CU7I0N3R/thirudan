from __future__ import annotations

from datetime import datetime
from bs4 import BeautifulSoup, Tag

import core.markup as markup
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
from core.utils import (
    convert_hex_to_html,
    decode_html_entities,
    find_reg_number,
    parse_float,
    parse_int,
)


class AcademiaParser:
    def parse_attendance(self, page_html: str) -> AttendanceResponse:
        reg_number = find_reg_number(page_html)
        try:
            table_html = markup.attendance_table(page_html)
        except Exception:
            return AttendanceResponse(regNumber=reg_number, attendance=[])

        soup = BeautifulSoup(table_html, "html.parser")
        cells = [
            cell
            for cell in soup.select("td[bgcolor='#E6E6FA']")
            if cell.get_text() != " - "
        ]
        attendance: list[Attendance] = []

        for cell in cells:
            course_code = cell.get_text(strip=True)
            if not (
                (len(course_code) > 10 and course_code[:1].isdigit())
                or "regular" in course_code.lower()
            ):
                continue

            siblings = _next_cells(cell)
            if len(siblings) < 7:
                continue

            conducted = siblings[5].get_text(strip=True)
            absent = siblings[6].get_text(strip=True)
            conducted_hours = parse_float(conducted)
            absent_hours = parse_float(absent)
            percentage = (
                ((conducted_hours - absent_hours) / conducted_hours * 100)
                if conducted_hours
                else 0.0
            )
            title = siblings[0].get_text(strip=True).split(" \\u2013")[0]
            if title.lower() == "null":
                continue

            attendance.append(
                Attendance(
                    courseCode=course_code.replace("Regular", ""),
                    courseTitle=title,
                    category=siblings[1].get_text(strip=True),
                    facultyName=siblings[2].get_text(strip=True),
                    slot=siblings[3].get_text(strip=True),
                    hoursConducted=conducted,
                    hoursAbsent=absent,
                    attendancePercentage=f"{percentage:.2f}",
                )
            )

        return AttendanceResponse(
            regNumber=reg_number, attendance=attendance, status=200
        )

    def parse_marks(self, page_html: str) -> MarksResponse:
        attendance = self.parse_attendance(page_html)
        course_map = {
            entry.courseCode: entry.courseTitle for entry in attendance.attendance
        }
        try:
            fragment = markup.marks_fragment(page_html)
        except Exception:
            return MarksResponse(regNumber=attendance.regNumber, marks=[], status=200)

        soup = BeautifulSoup(fragment, "html.parser")
        serialized = markup.normalize_marks_html(str(soup))
        table_parts = serialized.split("</table></td>")
        marks: list[Mark] = []

        for table_html in table_parts:
            table = BeautifulSoup(table_html, "html.parser")
            for row in table.find_all("tr"):
                cells = row.find_all("td", recursive=False)
                if len(cells) < 3:
                    continue

                course_code = cells[0].get_text(strip=True)
                course_type = cells[1].get_text(strip=True)
                performances: list[TestPerformance] = []
                overall_scored = 0.0
                overall_total = 0.0

                for test_cell in cells[2].select("table td"):
                    pieces = test_cell.get_text(strip=True).split(".00")
                    if len(pieces) < 2:
                        continue
                    name_parts = pieces[0].split("/")
                    if len(name_parts) < 2:
                        continue
                    test_title = name_parts[0]
                    total = parse_float(name_parts[1])
                    scored = parse_float(pieces[1])
                    performances.append(
                        TestPerformance(
                            test=test_title,
                            marks=MarksDetail(
                                scored="Abs" if pieces[1] == "Abs" else f"{scored:.2f}",
                                total=f"{total:.2f}",
                            ),
                        )
                    )
                    overall_scored += scored
                    overall_total += total

                marks.append(
                    Mark(
                        courseName=course_map.get(course_code, ""),
                        courseCode=course_code,
                        courseType=course_type,
                        overall=MarksDetail(
                            scored=f"{overall_scored:.2f}", total=f"{overall_total:.2f}"
                        ),
                        testPerformance=performances,
                    )
                )

        ordered = [mark for mark in marks if mark.courseType == "Theory"]
        ordered.extend(mark for mark in marks if mark.courseType == "Practical")
        return MarksResponse(regNumber=attendance.regNumber, marks=ordered, status=200)

    def parse_courses(self, page_html: str) -> CourseResponse:
        reg_number = find_reg_number(page_html)
        table_html = markup.course_table(page_html)
        soup = BeautifulSoup(table_html, "html.parser")
        courses: list[Course] = []

        for index, row in enumerate(soup.find_all("tr")):
            if index == 0:
                continue
            cells = row.find_all("td")
            course = self._parse_course_row(cells)
            if course:
                courses.append(course)

        return CourseResponse(regNumber=reg_number, courses=courses)

    def parse_user(self, page_html: str, now: datetime | None = None) -> User:
        table_html = markup.user_table(page_html)
        soup = BeautifulSoup(table_html, "html.parser")
        reg_number = find_reg_number(page_html)
        user = User(
            regNumber=reg_number, year=_student_year(reg_number, now or datetime.now())
        )

        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            for index in range(0, len(cells), 2):
                if index + 1 >= len(cells):
                    continue
                key = cells[index].get_text(strip=True).removesuffix(":")
                value_cell = cells[index + 1]
                value = value_cell.get_text(strip=True)
                if key == "Name":
                    user.name = value
                elif key == "Program":
                    user.program = value
                elif key == "Combo / Batch":
                    font = value_cell.find("font")
                    user.batch = font.get_text(strip=True) if font else ""
                elif key == "Mobile":
                    user.mobile = value
                elif key == "Semester":
                    user.semester = parse_int(value)
                elif key == "Department":
                    parts = value.split("-", 1)
                    user.department = parts[0].strip()
                    if len(parts) > 1:
                        user.section = (
                            parts[1].strip().removeprefix("(").removesuffix(" Section)")
                        )

        return user

    def parse_calendar(
        self, response_html: str, today: datetime | None = None
    ) -> CalendarResponse:
        if "<table bgcolor=" in response_html:
            html_text = response_html
        else:
            parts = response_html.split('zmlvalue="', 1)
            if len(parts) < 2:
                return CalendarResponse(
                    error=True, message="invalid HTML format", status=500, calendar=[]
                )
            encoded = parts[1].split('" > </div> </div>', 1)[0]
            html_text = decode_html_entities(convert_hex_to_html(encoded))

        soup = BeautifulSoup(html_text, "html.parser")
        headers = [
            heading.get_text(strip=True)
            for heading in soup.find_all("th")
            if "'2" in heading.get_text()
        ]
        months = [CalendarMonth(month=header, days=[]) for header in headers]

        for row in soup.select("table tr"):
            cells = row.find_all("td")
            for index, month in enumerate(months):
                offset = index * 5 if index > 0 else 0
                if len(cells) <= offset + 3:
                    continue
                date = cells[offset].get_text(strip=True)
                day = cells[offset + 1].get_text(strip=True)
                event = cells[offset + 2].get_text(strip=True)
                day_order = cells[offset + 3].get_text(strip=True)
                if date and day_order:
                    month.days.append(
                        Day(date=date, day=day, event=event, dayOrder=day_order)
                    )

        sorted_months = sort_calendar(months)
        return calendar_response_for_date(sorted_months, today or datetime.now())

    @staticmethod
    def _parse_course_row(cells: list[Tag]) -> Course | None:
        if len(cells) < 11:
            return None

        values = [cell.get_text(strip=True) for cell in cells]
        room = values[9] or "N/A"
        if room != "N/A":
            room = room[:1].upper() + room[1:]
        slot = values[8].removesuffix("-")

        return Course(
            code=values[1],
            title=values[2].split(" \\u2013")[0],
            credit=values[3] or "N/A",
            category=values[4],
            courseCategory=values[5],
            type=values[6] or "N/A",
            slotType="Practical" if "P" in slot else "Theory",
            faculty=values[7] or "N/A",
            slot=slot,
            room=room,
            academicYear=values[10],
        )


def sort_calendar(months: list[CalendarMonth]) -> list[CalendarMonth]:
    month_order = {
        name: index
        for index, name in enumerate(
            (
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            )
        )
    }

    def month_key(month: CalendarMonth) -> int:
        return month_order.get(month.month.split("'")[0][:3], 99)

    sorted_months = sorted(months, key=month_key)
    for month in sorted_months:
        month.days.sort(key=lambda day: parse_int(day.date))
    return sorted_months


def calendar_response_for_date(
    months: list[CalendarMonth], current: datetime
) -> CalendarResponse:
    if not months:
        return CalendarResponse(status=200, calendar=[])

    current_name = current.strftime("%b")
    month_index = next(
        (index for index, month in enumerate(months) if current_name in month.month), 0
    )
    month = months[month_index]
    today = None
    tomorrow = None

    if month.days:
        today_index = current.day - 1
        if 0 <= today_index < len(month.days):
            today = month.days[today_index]
            tomorrow_index = today_index + 1
            if tomorrow_index < len(month.days):
                tomorrow = month.days[tomorrow_index]
            elif month_index + 1 < len(months) and months[month_index + 1].days:
                tomorrow = months[month_index + 1].days[0]

    return CalendarResponse(
        status=200, today=today, tomorrow=tomorrow, index=month_index, calendar=months
    )


def _next_cells(cell: Tag) -> list[Tag]:
    siblings: list[Tag] = []
    for sibling in cell.next_siblings:
        if isinstance(sibling, Tag) and sibling.name == "td":
            siblings.append(sibling)
    return siblings


def _student_year(reg_number: str, now: datetime) -> int:
    if len(reg_number) < 4:
        return 0
    admission_year = parse_int(reg_number[2:4])
    academic_year = now.year % 100
    if now.month >= 7:
        academic_year += 1
    year = academic_year - admission_year
    if admission_year > now.year % 100:
        year -= 1
    return year
