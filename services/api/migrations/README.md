# Database migrations

Set `TEAMUP_DATABASE_URL` to a server-side `mysql+pymysql://...` connection string, then run from `services/api`:

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic downgrade base
```

The initial migration creates only identity/session, profile, project, role, and ordered tag tables. It does not import local memory data. Always verify downgrade against non-production data before relying on it as a recovery path.

To run the MySQL-specific integration test after upgrading an isolated test database:

```powershell
$env:TEAMUP_TEST_MYSQL_URL = "mysql+pymysql://<test-user>:<test-password>@<host>:3306/<test-database>?charset=utf8mb4"
python -m pytest -ra
```

The test URL must never target staging or production. Without this variable, the MySQL-specific test is skipped; SQLite tests do not replace MySQL verification.
