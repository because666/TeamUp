from datetime import timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db_models import Base, SessionRow, UserRow
from app.errors import ServiceError
from app.schemas import ProfilePayload, ProjectPayload, ProjectUpdate
from app.sql_store import SqlAlchemyStore, db_now, token_digest


def profile_payload(nickname: str = "林同学") -> ProfilePayload:
    return ProfilePayload(
        nickname=nickname,
        school="示例大学",
        major="计算机科学",
        grade="大三",
        skills=["Python", "MySQL"],
        collaborationScenarios=["竞赛"],
        rolePreference="FLEXIBLE",
        hoursPerWeek=8,
        bio="负责后端开发",
        visibility=True,
    )


def project_payload(title: str = "校园创新项目") -> ProjectPayload:
    return ProjectPayload.model_validate(
        {
            "title": title,
            "description": "为学生提供协作工具",
            "direction": "AI",
            "competition": "互联网+",
            "stage": "IDEA",
            "teamInfo": "已有产品同学",
            "roles": [
                {
                    "name": "后端开发",
                    "skills": ["Python"],
                    "headcount": 1,
                    "hoursPerWeek": 8,
                    "description": "",
                    "status": "OPEN",
                }
            ],
        }
    )


@pytest.fixture
def sql_store(tmp_path):
    database_path = tmp_path / "teamup-test.db"
    engine = create_engine(f"sqlite+pysqlite:///{database_path.as_posix()}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    try:
        yield SqlAlchemyStore(factory, engine), factory, engine
    finally:
        engine.dispose()


def assert_service_error(code: str, operation) -> None:
    with pytest.raises(ServiceError) as captured:
        operation()
    assert captured.value.code == code


def test_data_survives_store_recreation_and_subject_is_unique(sql_store) -> None:
    store, factory, engine = sql_store
    user_id, token, complete = store.login("wechat:app-a:openid-a")
    assert complete is False
    saved = store.save_profile(user_id, profile_payload(), 0)
    project = store.create_project(user_id, project_payload())

    recreated = SqlAlchemyStore(factory, engine)
    same_user_id, second_token, complete = recreated.login("wechat:app-a:openid-a")

    assert same_user_id == user_id
    assert second_token != token
    assert complete is True
    assert recreated.get_profile(user_id) == saved
    assert recreated.get_project(project.id) == project
    with factory() as session:
        assert len(session.scalars(select(UserRow)).all()) == 1


def test_token_is_hashed_and_logout_revokes_session(sql_store) -> None:
    store, factory, _ = sql_store
    user_id, token, _ = store.login("wechat:app-a:openid-a")

    with factory() as session:
        row = session.scalar(select(SessionRow))
        assert row is not None
        assert row.user_id == user_id
        assert row.token_digest == token_digest(token)
        assert token not in row.token_digest

    store.logout(token)
    assert_service_error("SESSION_EXPIRED", lambda: store.user_for_token(token))


def test_expired_session_is_rejected(sql_store) -> None:
    store, factory, _ = sql_store
    _, token, _ = store.login("wechat:app-a:openid-a")
    with factory.begin() as session:
        row = session.scalar(select(SessionRow))
        assert row is not None
        row.expires_at = db_now() - timedelta(seconds=1)

    assert_service_error("SESSION_EXPIRED", lambda: store.user_for_token(token))


def test_profile_version_conflict(sql_store) -> None:
    store, _, _ = sql_store
    user_id, _, _ = store.login("wechat:app-a:openid-a")
    created = store.save_profile(user_id, profile_payload(), 0)
    updated = store.save_profile(user_id, profile_payload("新昵称"), created.version)

    assert updated.version == 2
    assert updated.nickname == "新昵称"
    assert_service_error(
        "VERSION_CONFLICT",
        lambda: store.save_profile(user_id, profile_payload("过期更新"), created.version),
    )


def test_project_owner_version_roles_and_pagination(sql_store) -> None:
    store, _, _ = sql_store
    owner_id, _, _ = store.login("wechat:app-a:owner")
    other_id, _, _ = store.login("wechat:app-a:other")
    first = store.create_project(owner_id, project_payload("第一个项目"))

    assert_service_error(
        "FORBIDDEN",
        lambda: store.update_project(
            other_id, first.id, ProjectUpdate(**project_payload().model_dump(), version=first.version)
        ),
    )

    replacement = project_payload("更新后的项目").model_dump()
    replacement["roles"] = [
        {
            "name": "产品经理",
            "skills": ["需求分析", "原型设计"],
            "headcount": 2,
            "hoursPerWeek": 6,
            "description": "负责产品",
            "status": "OPEN",
        },
        {
            "name": "测试",
            "skills": ["Pytest"],
            "headcount": 1,
            "hoursPerWeek": 4,
            "description": "负责质量",
            "status": "OPEN",
        },
    ]
    updated = store.update_project(owner_id, first.id, ProjectUpdate(**replacement, version=first.version))
    assert updated.version == 2
    assert [role.name for role in updated.roles] == ["产品经理", "测试"]
    assert_service_error(
        "VERSION_CONFLICT",
        lambda: store.update_project(owner_id, first.id, ProjectUpdate(**replacement, version=first.version)),
    )

    published_first = store.publish_project(owner_id, updated.id, updated.version)
    second = store.create_project(owner_id, project_payload("第二个项目"))
    published_second = store.publish_project(owner_id, second.id, second.version)
    first_page, cursor = store.list_projects("PUBLISHED", 1, None)
    second_page, next_cursor = store.list_projects("PUBLISHED", 1, cursor)

    assert {first_page[0].id, second_page[0].id} == {published_first.id, published_second.id}
    assert cursor is not None
    assert next_cursor is None
