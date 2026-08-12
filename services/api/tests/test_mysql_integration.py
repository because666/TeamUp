import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db_models import SessionRow
from app.errors import ServiceError
from app.main import make_app
from app.schemas import MatchPreferencesPayload, ProfilePayload, ProjectPayload, ProjectUpdate
from app.sql_store import SqlAlchemyStore, token_digest


MYSQL_URL = os.getenv("TEAMUP_TEST_MYSQL_URL")
pytestmark = pytest.mark.skipif(not MYSQL_URL, reason="TEAMUP_TEST_MYSQL_URL is not configured")


def profile_payload(nickname: str) -> ProfilePayload:
    return ProfilePayload(
        nickname=nickname,
        school="示例大学",
        major="计算机科学",
        grade="大三",
        skills=["Python"],
        collaborationScenarios=["竞赛"],
        rolePreference="FLEXIBLE",
        hoursPerWeek=8,
        visibility=True,
    )


def project_payload() -> ProjectPayload:
    return ProjectPayload.model_validate(
        {
            "title": "MySQL 集成项目",
            "description": "验证项目和岗位持久化",
            "direction": "后端",
            "stage": "IDEA",
            "collaborationScenarios": ["竞赛"],
            "roles": [
                {
                    "name": "后端开发",
                    "skills": ["Python", "MySQL"],
                    "requiredSkills": ["Python"],
                    "requiredAvailabilitySlots": [
                        {"weekday": 6, "startMinute": 540, "endMinute": 720}
                    ],
                    "collaborationRole": "MEMBER",
                    "headcount": 1,
                    "hoursPerWeek": 8,
                }
            ],
        }
    )


def test_mysql_persistence_token_digest_and_concurrent_profile_creation() -> None:
    assert MYSQL_URL is not None
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    store = SqlAlchemyStore(factory, engine)
    subject = f"wechat:integration:{uuid4().hex}"

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            login_outcomes = list(executor.map(store.login, [subject, subject]))
        assert login_outcomes[0][0] == login_outcomes[1][0]
        assert login_outcomes[0][1] != login_outcomes[1][1]
        assert login_outcomes[0][2] is False
        assert login_outcomes[1][2] is False
        user_id, token, _ = login_outcomes[0]
        with factory() as session:
            session_row = session.scalar(
                select(SessionRow).where(SessionRow.token_digest == token_digest(token))
            )
            assert session_row is not None
            assert session_row.token_digest == token_digest(token)
            assert token not in session_row.token_digest

        def save(nickname: str):
            try:
                return store.save_profile(user_id, profile_payload(nickname), 0)
            except ServiceError as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(save, ["并发用户甲", "并发用户乙"]))

        successes = [outcome for outcome in outcomes if not isinstance(outcome, ServiceError)]
        failures = [outcome for outcome in outcomes if isinstance(outcome, ServiceError)]
        assert len(successes) == 1
        assert [error.code for error in failures] == ["VERSION_CONFLICT"]

        updated_profile = store.save_profile(user_id, profile_payload("持久化更新"), successes[0].version)
        preferences = store.save_match_preferences(
            user_id,
            MatchPreferencesPayload.model_validate(
                {
                    "desiredDirections": ["后端", "AI"],
                    "availabilitySlots": [
                        {"weekday": 6, "startMinute": 540, "endMinute": 720}
                    ],
                }
            ),
            0,
        )

        project = store.create_project(user_id, project_payload())
        replacement = project_payload().model_dump()
        replacement["title"] = "更新后的 MySQL 项目"
        replacement["roles"] = [
            {
                "name": "测试工程师",
                "skills": ["Python", "Pytest"],
                "headcount": 2,
                "hoursPerWeek": 6,
                "description": "验证岗位替换",
                "status": "OPEN",
            }
        ]
        updated_project = store.update_project(
            user_id,
            project.id,
            ProjectUpdate(**replacement, version=project.version),
        )
        published = store.publish_project(user_id, project.id, updated_project.version)

        recreated = SqlAlchemyStore(factory, engine)
        assert recreated.user_for_token(token) == user_id
        assert recreated.get_profile(user_id) == updated_profile
        assert recreated.get_match_preferences(user_id) == preferences
        assert recreated.get_project(project.id) == published
        assert published.collaborationScenarios == ["竞赛"]
        assert published.roles[0].requiredSkills == ["Python"]
    finally:
        engine.dispose()


def test_mysql_backed_api_survives_app_recreation() -> None:
    assert MYSQL_URL is not None
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    settings = Settings(environment="test", store_backend="mysql", database_url=MYSQL_URL)
    code = f"local:mysql-api-{uuid4().hex}"

    try:
        with TestClient(make_app(settings, store_override=SqlAlchemyStore(factory, engine))) as first_client:
            login_response = first_client.post(
                "/api/v1/auth/wechat/login",
                json={"code": code, "consentAccepted": True},
            )
            assert login_response.status_code == 200
            token = login_response.json()["data"]["accessToken"]
            headers = {"Authorization": f"Bearer {token}"}
            profile_response = first_client.put(
                "/api/v1/me/profile",
                headers=headers,
                json={**profile_payload("接口用户").model_dump(), "version": 0},
            )
            assert profile_response.status_code == 200
            project_response = first_client.post(
                "/api/v1/projects",
                headers=headers,
                json=project_payload().model_dump(),
            )
            assert project_response.status_code == 200
            project_id = project_response.json()["data"]["id"]

        with TestClient(make_app(settings, store_override=SqlAlchemyStore(factory, engine))) as recreated_client:
            profile = recreated_client.get("/api/v1/me/profile", headers=headers)
            assert profile.json()["data"]["nickname"] == "接口用户"
            assert recreated_client.get(f"/api/v1/projects/{project_id}", headers=headers).status_code == 200
    finally:
        engine.dispose()


def test_mysql_concurrent_members_cannot_overfill_role() -> None:
    assert MYSQL_URL is not None
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    store = SqlAlchemyStore(factory, engine)
    suffix = uuid4().hex
    owner_id, _, _ = store.login(f"wechat:integration:capacity-owner:{suffix}")
    first_user_id, _, _ = store.login(f"wechat:integration:capacity-first:{suffix}")
    second_user_id, _, _ = store.login(f"wechat:integration:capacity-second:{suffix}")

    try:
        draft = store.create_project(owner_id, project_payload())
        published = store.publish_project(owner_id, draft.id, draft.version)
        role_id = published.roles[0].id

        def add(user_id: str):
            try:
                return store.add_project_member(published.id, role_id, user_id)
            except ServiceError as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(add, [first_user_id, second_user_id]))

        successes = [outcome for outcome in outcomes if not isinstance(outcome, ServiceError)]
        failures = [outcome for outcome in outcomes if isinstance(outcome, ServiceError)]
        assert len(successes) == 1
        assert [error.code for error in failures] == ["ROLE_FULL"]
        assert len(store.list_project_members(owner_id, published.id)) == 1
        refreshed = store.get_project(published.id)
        assert refreshed.roles[0].filledCount == 1
        assert refreshed.roles[0].remainingCount == 0
    finally:
        engine.dispose()


def test_mysql_block_persistence_and_member_blocking() -> None:
    assert MYSQL_URL is not None
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    store = SqlAlchemyStore(factory, engine)
    suffix = uuid4().hex
    owner_id, _, _ = store.login(f"wechat:integration:block-owner:{suffix}")
    member_id, _, _ = store.login(f"wechat:integration:block-member:{suffix}")
    try:
        block = store.create_block(owner_id, member_id)
        recreated = SqlAlchemyStore(factory, engine)
        assert recreated.users_blocked(owner_id, member_id) is True
        assert recreated.create_block(owner_id, member_id) == block
        draft = recreated.create_project(owner_id, project_payload())
        published = recreated.publish_project(owner_id, draft.id, draft.version)
        with pytest.raises(ServiceError) as captured:
            recreated.add_project_member(published.id, published.roles[0].id, member_id)
        assert captured.value.code == "USER_BLOCKED"
        assert recreated.remove_block(owner_id, member_id) is True
        assert recreated.users_blocked(owner_id, member_id) is False
        assert recreated.add_project_member(published.id, published.roles[0].id, member_id).userId == member_id
    finally:
        engine.dispose()


def test_mysql_invitations_persist_and_concurrent_accept_cannot_overfill() -> None:
    assert MYSQL_URL is not None
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    store = SqlAlchemyStore(factory, engine)
    suffix = uuid4().hex
    owner_id, _, _ = store.login(f"wechat:integration:invite-owner:{suffix}")
    first_id, _, _ = store.login(f"wechat:integration:invite-first:{suffix}")
    second_id, _, _ = store.login(f"wechat:integration:invite-second:{suffix}")
    try:
        draft = store.create_project(owner_id, project_payload())
        published = store.publish_project(owner_id, draft.id, draft.version)
        role_id = published.roles[0].id
        first = store.create_invitation(owner_id, published.id, role_id, first_id)
        second = store.create_invitation(owner_id, published.id, role_id, second_id)

        recreated = SqlAlchemyStore(factory, engine)
        assert recreated.create_invitation(owner_id, published.id, role_id, first_id) == first

        def accept(invitee_and_invitation):
            invitee_id, invitation_id = invitee_and_invitation
            try:
                return recreated.accept_invitation(invitee_id, invitation_id)
            except ServiceError as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(
                executor.map(
                    accept,
                    [(first_id, first.id), (second_id, second.id)],
                )
            )

        successes = [outcome for outcome in outcomes if not isinstance(outcome, ServiceError)]
        failures = [outcome for outcome in outcomes if isinstance(outcome, ServiceError)]
        assert len(successes) == 1
        assert [error.code for error in failures] == ["ROLE_FULL"]
        assert len(recreated.list_project_members(owner_id, published.id)) == 1

        blocked_project = recreated.create_project(owner_id, project_payload())
        blocked_project = recreated.publish_project(owner_id, blocked_project.id, blocked_project.version)
        blocked_invitation = recreated.create_invitation(
            owner_id, blocked_project.id, blocked_project.roles[0].id, second_id
        )
        recreated.create_block(second_id, owner_id)
        with pytest.raises(ServiceError) as captured:
            recreated.accept_invitation(second_id, blocked_invitation.id)
        assert captured.value.code == "USER_BLOCKED"
    finally:
        engine.dispose()
