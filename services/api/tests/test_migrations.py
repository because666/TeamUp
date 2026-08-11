from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


EXPECTED_TABLES = {
    "alembic_version",
    "users",
    "sessions",
    "profiles",
    "profile_skills",
    "profile_collaboration_scenarios",
    "projects",
    "project_roles",
    "project_role_skills",
}


def test_initial_migration_upgrades_and_downgrades(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("TEAMUP_DATABASE_URL", raising=False)
    database_path = tmp_path / "migration-test.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES
        command.downgrade(config, "base")
        assert inspect(engine).get_table_names() == ["alembic_version"]
    finally:
        engine.dispose()
