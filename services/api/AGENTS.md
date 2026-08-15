# Backend Service Instructions

- Run commands from `services/api` with the locked Python dependencies in `pyproject.toml`.
- Local container verification uses `docker build -t teamup-api:cloudbase-spike .`; no image push or cloud deployment without an accepted deployment decision and current user approval.
- The foundation uses an explicit in-memory store for local/test only; do not enable it in production.
- CloudBase staging/production must inject MySQL and WeChat configuration through the service secret/environment controls; never bake values into the image or commit a populated environment file.
- Keep authentication, ownership checks, request validation, and response envelopes in the service layer.
- Add or update tests for every endpoint or behavior change.
- Do not log bearer tokens, WeChat credentials, private message content, or environment secrets.
