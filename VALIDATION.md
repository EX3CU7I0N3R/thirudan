# Validation

Latest local checks:

- Python modules compile successfully.
- FastAPI app imports successfully from `web.api`.
- Package-style imports from the parent workspace resolve successfully.
- `/hello` returns `{"message": "Hello, World!"}` through the test client.
- Missing `X-CSRF-Token` returns a direct `401` JSON error.
- Invalid `/login` JSON returns a direct `400` JSON error.
- Implementation files are grouped under `core`, `scraper`, `services`, and `web`.
- Response schemas are split by domain under `core/schemas`.
- Dev-mode and the extra app-level bearer gate have been removed; protected scraper routes require only the SRM session cookie header.
- Security hardening pass added bounded cache, request-size limits, safer CORS defaults, generic 500s, session-only tester storage, and security headers.

Live SRM Academia checks require valid credentials or an active session cookie. Persistent cache checks require Supabase environment variables.
