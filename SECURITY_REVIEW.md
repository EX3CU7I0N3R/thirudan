# Security Review

Latest local review covered API exposure, CORS behavior, session handling, request sizing, route caching, generic error handling, response headers, rate limiting, outbound HTTP, and optional persistence.

## Changes Applied

- Removed always-on `file://` CORS support. `ALLOW_FILE_ORIGIN=true` is now required for local file-based tester use.
- Changed tester session handling from `localStorage` to `sessionStorage`.
- Hashed session cookies before using them as in-memory cache keys.
- Added security response headers:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Cache-Control: no-store`
- Added request body size enforcement via `MAX_REQUEST_BODY_BYTES`.
- Bounded in-memory route cache via `CACHE_MAX_ENTRIES`.
- Replaced detailed unexpected exception output with a generic `Internal server error`.
- Replaced the unprofessional rate-limit response body with a neutral message.
- Added `.gitignore`, `.env.example`, and `SECURITY.md` for safer public release handling.
- Ran `pip-audit -r requirements.txt`; no known vulnerabilities were found.

## Residual Risks

- The SRM session cookie is still sent by callers in `X-CSRF-Token`; treat it as a credential.
- The HTML tester is for local manual testing only.
- Persistent cache storage requires careful Supabase row-level access rules outside this codebase.
- Live scraping reliability still depends on SRM endpoint behavior and account/session validity.
