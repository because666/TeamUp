from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


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
    "match_preferences",
    "match_preference_directions",
    "match_preference_availability_slots",
    "project_collaboration_scenarios",
    "project_role_availability_slots",
    "project_members",
    "blocks",
    "invitations",
    "conversations",
    "conversation_participants",
    "messages",
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
        assert {column["name"] for column in inspect(engine).get_columns("project_roles")} >= {
            "collaboration_role"
        }
        assert {column["name"] for column in inspect(engine).get_columns("project_role_skills")} >= {
            "required"
        }
        member_foreign_keys = inspect(engine).get_foreign_keys("project_members")
        assert any(
            foreign_key["constrained_columns"] == ["project_id", "role_id"]
            and foreign_key["referred_table"] == "project_roles"
            and foreign_key["referred_columns"] == ["project_id", "id"]
            for foreign_key in member_foreign_keys
        )
        invitation_foreign_keys = inspect(engine).get_foreign_keys("invitations")
        assert any(
            foreign_key["constrained_columns"] == ["project_id", "role_id"]
            and foreign_key["referred_table"] == "project_roles"
            and foreign_key["referred_columns"] == ["project_id", "id"]
            for foreign_key in invitation_foreign_keys
        )
        message_foreign_keys = inspect(engine).get_foreign_keys("messages")
        assert any(
            foreign_key["constrained_columns"] == ["conversation_id", "sender_id"]
            and foreign_key["referred_table"] == "conversation_participants"
            and foreign_key["referred_columns"] == ["conversation_id", "user_id"]
            for foreign_key in message_foreign_keys
        )
        command.check(config)
        command.downgrade(config, "base")
        assert inspect(engine).get_table_names() == ["alembic_version"]
    finally:
        engine.dispose()


def test_existing_role_skills_migrate_as_bonus(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("TEAMUP_DATABASE_URL", raising=False)
    database_path = tmp_path / "migration-existing.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "20260811_0001")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users "
                    "(id, wechat_subject, status, created_at, updated_at) "
                    "VALUES ('usr_existing', 'local:existing', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO projects "
                    "(id, owner_id, title, description, direction, competition, stage, team_info, "
                    "status, version, published_at, created_at, updated_at) "
                    "VALUES ('prj_existing', 'usr_existing', '旧项目', '旧项目描述', 'AI', '', 'IDEA', '', "
                    "'DRAFT', 1, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO project_roles "
                    "(id, project_id, position, name, headcount, hours_per_week, description, status) "
                    "VALUES ('role_existing', 'prj_existing', 0, '后端', 1, 8, '', 'OPEN')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO project_role_skills (role_id, position, skill_name) "
                    "VALUES ('role_existing', 0, 'Python')"
                )
            )

        command.upgrade(config, "head")
        with engine.connect() as connection:
            required = connection.execute(
                text("SELECT required FROM project_role_skills WHERE role_id = 'role_existing'")
            ).scalar_one()
            collaboration_role = connection.execute(
                text("SELECT collaboration_role FROM project_roles WHERE id = 'role_existing'")
            ).scalar_one()
        assert required in (False, 0)
        assert collaboration_role == "MEMBER"
    finally:
        engine.dispose()
