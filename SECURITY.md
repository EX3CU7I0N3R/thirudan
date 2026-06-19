# Security

Thirudan is intended for local, user-controlled scraping sessions. Do not run a shared public instance that accepts other users' SRM Academia credentials.

## Sensitive Data

- SRM passwords are sent only to the local API, which forwards them to SRM Academia during login.
- The `X-CSRF-Token` header contains the active SRM session cookie. Treat it like a password.
- The browser tester stores the session cookie in `sessionStorage`, so it is cleared when the tab session ends.
- `.env` is ignored by Git. Use `.env.example` as the public template.

## Reporting

If you find a security issue, open a private report or contact the maintainer directly. Avoid posting working credentials, session cookies, or live portal responses in public issues.
