# Publishing Checklist

Use `thirudan` as the repository root.

## Before Uploading

- Keep `.env` local. Publish `.env.example`.
- Do not include screenshots or logs that show SRM credentials, cookies, captcha digests, student IDs, or live portal payloads.
- Keep the project description clear: "Local unofficial SRM Academia API scraper."
- Add GitHub topics such as `srm`, `academia`, `fastapi`, `scraper`, and `student-tools`.
- Avoid hosting a public instance that accepts other users' credentials.

## Suggested Commands

```powershell
git init
git add .
git commit -m "Prepare Thirudan for public release"
git branch -M main
git remote add origin https://github.com/<your-username>/thirudan.git
git push -u origin main
```

## Suggested Repository Summary

Thirudan is a local FastAPI service that logs into SRM Academia and normalizes attendance, marks, courses, profile, calendar, and timetable data into API responses.
