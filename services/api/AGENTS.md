# Backend Service Instructions

- Run commands from `services/api` with the locked Python dependencies in `pyproject.toml`.
- The foundation uses an explicit in-memory store for local/test only; do not enable it in production.
- Keep authentication, ownership checks, request validation, and response envelopes in the service layer.
- Add or update tests for every endpoint or behavior change.
- Do not log bearer tokens, WeChat credentials, private message content, or environment secrets.

