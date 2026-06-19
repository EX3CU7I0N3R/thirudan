from __future__ import annotations

import re

from core.constants import ATTENDANCE_TABLE, COURSE_TABLE, MARKS_TABLE, USER_TABLE
from core.exceptions import ParseError
from core.utils import convert_hex_to_html


def extract_sanitized_html(response_text: str, context: str) -> str:
    parts = response_text.split(".sanitize('", 1)
    if len(parts) < 2:
        raise ParseError(f"{context} - invalid response format")
    html_hex = parts[1].split("')", 1)[0]
    return convert_hex_to_html(html_hex)


def slice_between(value: str, start: str, end: str, context: str) -> str:
    parts = value.split(start, 1)
    if len(parts) < 2:
        raise ParseError(f"{context} table not found")
    body = parts[1].split(end, 1)[0]
    return f"{start}{body}{end}"


def attendance_table(html: str) -> str:
    cleaned = html.replace(
        "<td  bgcolor='#E6E6FA' style='text-align:center'> - </td>", ""
    )
    return slice_between(cleaned, ATTENDANCE_TABLE, "</table>", "attendance")


def course_table(html: str) -> str:
    body = slice_between(html, COURSE_TABLE, "</table>", "course")
    inner = body.removeprefix(COURSE_TABLE).removesuffix("</table>")
    return f"{ATTENDANCE_TABLE}<tbody>{inner}</tbody></table>"


def user_table(html: str) -> str:
    return slice_between(html, USER_TABLE, "</table>", "user")


def marks_fragment(html: str) -> str:
    parts = html.split(MARKS_TABLE, 1)
    if len(parts) < 2:
        raise ParseError("marks table not found")
    body = parts[1].split(
        '<table  width=800px;"border="0"cellspacing="1"cellpadding="1">', 1
    )[0]
    body = body.split("<br />", 1)[0]
    return f"{MARKS_TABLE}{body}"


def normalize_marks_html(html: str) -> str:
    cleaned = re.sub(r"\s+", " ", html)
    return cleaned.replace(
        '<table style="font-size" :6;="" border="2" cellpadding="1" cellspacing="1"><tbody><tr><td>',
        "",
    ).replace("</td></tr>", "")
