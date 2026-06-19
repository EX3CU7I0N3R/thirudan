from __future__ import annotations

from core.config import settings

BASE_URL = settings.academia_base_url
PORTAL_ID = settings.portal_id
SERVICE_NAME = settings.service_name

SIGNIN_URL = f"{BASE_URL}/accounts/signin.ac"
LOGOUT_URL = (
    f"{BASE_URL}/accounts/p/{PORTAL_ID}/logout"
    f"?servicename={SERVICE_NAME}&serviceurl={BASE_URL}"
)
ACTIVE_SESSIONS_URL = f"{BASE_URL}/accounts/p/{PORTAL_ID}/webclient/v1/account/self/user/self/activesessions"
CAPTCHA_URL = f"{BASE_URL}/accounts/p/40-{PORTAL_ID}/webclient/v1/captcha/{{cdigest}}?darkmode=false"

ATTENDANCE_PAGE = f"{BASE_URL}/srm_university/academia-academic-services/page/{settings.attendance_page_name}"
COURSE_PAGE = f"{BASE_URL}/srm_university/academia-academic-services/page/{settings.course_page_name}"
CALENDAR_PAGE = f"{BASE_URL}/srm_university/academia-academic-services/page/{settings.calendar_page_name}"

BROWSER_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": f"{BASE_URL}/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "dnt": "1",
    "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-gpc": "1",
}

ATTENDANCE_TABLE = (
    '<table style="font-size :16px;" border="1" align="center" '
    'cellpadding="1" cellspacing="1" bgcolor="#FAFAD2">'
)
COURSE_TABLE = (
    '<table cellspacing="1" cellpadding="1" border="1" align="center" '
    'style="width:900px!important;" class="course_tbl">'
)
USER_TABLE = '<table border="0" align="left" cellpadding="1" cellspacing="1" style="width:900px;">'
MARKS_TABLE = '<table border="1" align="center" cellpadding="1" cellspacing="1">'
