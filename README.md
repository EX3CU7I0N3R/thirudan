# Thirudan

Python 3.11+ service for fetching and normalizing SRM Academia data for local use.

The service is organized into a few small module groups, with `main.py` as the entrypoint.

## Status

Thirudan is an unofficial project and is not affiliated with SRM Institute of Science and Technology or Zoho. Use it only with your own account, respect the portal's terms, and do not deploy it as a shared credential-collection service.

## Run

```powershell
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env
.\venv\Scripts\python main.py
```

The server listens on `PORT` or `8080`.

Open `scraper_check.html` in a browser for a minimal manual tester. Keep the API running while using it.

For safer browser testing, serve the folder over localhost instead of opening the file directly:

```powershell
python -m http.server 8081
```

Then set `URL=http://localhost:8081` in `.env` and open `http://localhost:8081/scraper_check.html`. If you intentionally want to open the tester as `file://`, set `ALLOW_FILE_ORIGIN=true` only while testing locally.

## Scraper Check HTML

`scraper_check.html` is a browser-only tester for calling the local API without writing curl commands.

Fields:

- `API base URL`: Base address of the running Thirudan API. Use `http://localhost:8080` unless you changed `PORT`.
- `Account`: Your SRM Academia account identifier. You can enter the short account name, such as `aa1111`, or a full email address. The backend adds the SRM domain when needed.
- `Password`: SRM Academia password for the account.
- `Captcha digest`: Filled manually only when login returns a captcha challenge. The login response includes `captcha.cdigest`.
- `Captcha text`: The captcha solution you read from the captcha image URL returned by login.
- `X-CSRF-Token / session cookie`: The active SRM session cookie string. A successful login fills this automatically. You can also paste an existing cookie string here and call scraper endpoints directly.
- `Response`: Raw status and JSON body from the last request. A route can return HTTP `200` with an error-shaped body if SRM returned an unexpected page or the session is stale, so inspect this area after every request.

Buttons:

- `Hello`: Checks whether the API is reachable.
- `Login`: Sends account, password, and optional captcha fields to `/login`. On success, stores the session cookie in the `X-CSRF-Token / session cookie` field and browser session storage.
- `Attendance`: Calls `/attendance` with the current session cookie.
- `Marks`: Calls `/marks` with the current session cookie.
- `Courses`: Calls `/courses` with the current session cookie.
- `User`: Calls `/user` with the current session cookie.
- `Calendar`: Calls `/calendar` with the current session cookie.
- `Timetable`: Calls `/timetable` with the current session cookie.
- `Get All`: Calls `/get`, which fetches the aggregate user, attendance, marks, courses, and timetable payload.
- `Logout`: Calls `/logout` with the current session cookie.
- `Clear`: Clears only the response panel.

Typical flow:

1. Start the API with `python .\main.py`.
2. Open `scraper_check.html`.
3. Click `Hello`; expect `200` and `{"message": "Hello, World!"}`.
4. Enter `Account` and `Password`, then click `Login`.
5. If the response includes `captcha`, open `captcha.image`, enter `captcha.cdigest` and the solved `Captcha text`, then click `Login` again.
6. After login succeeds, call `Attendance`, `Marks`, `Courses`, `User`, `Calendar`, `Timetable`, or `Get All`.

## API

- `GET /hello`
- `POST /login`
- `DELETE /logout`
- `GET /attendance`
- `GET /marks`
- `GET /courses`
- `GET /user`
- `GET /calendar`
- `GET /timetable`
- `GET /get`

All routes except `/hello` and `/login` require `X-CSRF-Token`, which is the SRM Academia cookie string returned by login.

## Modules

- `web/`: FastAPI routes, CORS, compression, route caching, and rate-limit wiring.
- `services/`: login/logout, request auth validation, and optional snapshot persistence.
- `scraper/`: HTTP transport, HTML parsers, timetable derivation, and scraper workflow orchestration.
- `core/`: configuration, constants, markup helpers, rate limiting, cookies, shared utilities, and domain schemas.
- `core/schemas/`: response shapes split by academics, calendar, session, and timetable concerns.

## Environment

Configuration lives in `.env`. Start from `.env.example`; do not commit a populated `.env`.

Runtime:

- `PORT`: API port. Defaults to `8080`.
- `URL`: Optional comma-separated CORS origins.
- `ALLOW_FILE_ORIGIN`: Allows `file://` tester pages by accepting browser origin `null`. Keep `false` unless testing locally.
- `REQUEST_TIMEOUT`: Outbound SRM/Supabase request timeout in seconds.
- `CACHE_TTL_SECONDS`: In-memory route cache lifetime in seconds.
- `CACHE_MAX_ENTRIES`: Maximum number of in-memory cached route responses.
- `MAX_REQUEST_BODY_BYTES`: Maximum accepted request body size.

SRM Academia:

- `ACADEMIA_BASE_URL`: SRM Academia host.
- `ACADEMIA_PORTAL_ID`: Portal identifier used by login, logout, captcha, and session cleanup.
- `ACADEMIA_SERVICE_NAME`: Service name sent during login.
- `ATTENDANCE_PAGE_NAME`: Academia page name for attendance and marks.
- `COURSE_PAGE_NAME`: Academia page name for courses, user profile, and timetable derivation.
- `CALENDAR_PAGE_NAME`: Academia page name for academic planner data.

Persistence:

- `SUPABASE_URL`, `SUPABASE_KEY`, `ENCRYPTION_KEY`: Optional for local scraping, required for persistent snapshot cache behavior.
- `SCRAPE_TABLE`: Supabase table for aggregate scrape cache data.
- `CALENDAR_TABLE`: Supabase table for calendar cache data.
- `STUDENT_KEY_COLUMN`: Column used as the student identifier in the aggregate cache table.
- `SESSION_KEY_COLUMN`: Column used for the hashed session key in the aggregate cache table.
- `REFRESHED_AT_COLUMN`: Column used for the last refresh timestamp in the aggregate cache table.
- `SCHEDULE_NOTE_COLUMN`: Optional column for a schedule/operating-hours note surfaced as `scheduleNote`.

## Scraper Flow

Login posts credentials to SRM Academia and returns a reusable cookie header after the session is established. Captcha responses include the digest and captcha image URL so the caller can retry with a solved challenge.

Attendance and marks share the same Academia page. The service decodes the embedded escaped HTML payload, extracts the attendance table, then derives marks from the nested marks section while preserving course ordering.

Courses and user profile data share the timetable page. Timetable output is derived from parsed courses, the user's batch value, and the configured slot matrices.

Calendar uses the academic planner endpoint, supports both raw table HTML and encoded payloads, sorts months and days, and computes `today`, `tomorrow`, and the current month index.

## Validation

Local checks used during the latest refactor:

```powershell
.\venv\Scripts\python.exe -m compileall .
.\venv\Scripts\python.exe -c "from web.api import app; print(app.title)"
.\venv\Scripts\python.exe -c "from web.api import app; from fastapi.testclient import TestClient; c=TestClient(app); print(c.get('/hello').json())"
```

## License

MIT. See `LICENSE`.
