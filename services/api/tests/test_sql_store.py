from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db_models import (
    AccountDeletionRequestRow,
    AuditEventRow,
    Base,
    InvitationRow,
    RecommendationImpressionRow,
    SessionRow,
    UserRow,
)
from app.errors import ServiceError
from app.schemas import (
    MatchPreferencesPayload,
    ProfilePayload,
    ProjectPayload,
    ProjectUpdate,
    RecommendationImpressionItem,
    RecommendationImpressionRequest,
    ReportRequest,
)
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

    store.logout(token, "req_sql_logout")
    assert_service_error("SESSION_EXPIRED", lambda: store.user_for_token(token))
    with factory() as session:
        event = session.scalar(select(AuditEventRow).where(AuditEventRow.action == "LOGOUT"))
        assert event is not None
        assert event.request_id == "req_sql_logout"
        assert event.resource_type == "SESSION"


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


def test_discovery_queries_filter_public_profiles_and_owned_projects(sql_store) -> None:
    store, _, _ = sql_store
    owner_id, _, _ = store.login("wechat:app-a:discovery-owner")
    candidate_id, _, _ = store.login("wechat:app-a:discovery-candidate")
    viewer_id, _, _ = store.login("wechat:app-a:discovery-viewer")
    store.save_profile(candidate_id, profile_payload(), 0)
    store.save_match_preferences(
        candidate_id,
        MatchPreferencesPayload.model_validate({"desiredDirections": ["AI"], "availabilitySlots": []}),
        0,
    )
    project = store.create_project(owner_id, project_payload())
    published = store.publish_project(owner_id, project.id, project.version)

    profiles, profile_cursor = store.list_public_profiles(
        viewer_id, 20, None, "python", "ai", "FLEXIBLE", 6, 10
    )
    assert profile_cursor is None
    assert [item.id for item in profiles] == [candidate_id]
    assert store.get_public_profile(viewer_id, candidate_id).id == candidate_id
    mine, mine_cursor = store.list_my_projects(owner_id, "PUBLISHED", 20, None)
    assert mine_cursor is None
    assert [item.id for item in mine] == [published.id]

    store.create_block(candidate_id, viewer_id)
    assert_service_error("RESOURCE_NOT_FOUND", lambda: store.get_public_profile(viewer_id, candidate_id))
    profiles, _ = store.list_public_profiles(viewer_id, 20, None, None, None, None, None, None)
    assert profiles == []

    store.request_account_deletion(candidate_id, "req_discovery_candidate_deletion")
    assert_service_error("RESOURCE_NOT_FOUND", lambda: store.get_public_profile(owner_id, candidate_id))
    profiles, _ = store.list_public_profiles(owner_id, 20, None, None, None, None, None, None)
    assert candidate_id not in {profile.id for profile in profiles}


def test_rule_matching_store_returns_explanations_and_enforces_hard_constraints(sql_store) -> None:
    store, _, _ = sql_store
    owner_id, _, _ = store.login("wechat:app-a:match-owner")
    candidate_id, _, _ = store.login("wechat:app-a:match-candidate")
    candidate_payload = profile_payload()
    store.save_profile(candidate_id, candidate_payload, 0)
    store.save_match_preferences(
        candidate_id,
        MatchPreferencesPayload.model_validate({"desiredDirections": ["AI"], "availabilitySlots": []}),
        0,
    )
    project = store.create_project(owner_id, project_payload())
    published = store.publish_project(owner_id, project.id, project.version)
    role_id = published.roles[0].id
    results, cursor, request_id = store.project_matches(owner_id, published.id, role_id, 1, None)
    assert request_id.startswith("rrq_")
    assert cursor is None
    assert results[0].targetId == candidate_id
    assert results[0].targetType == "PROFILE"
    assert results[0].engineVersion == "match-v0.1"
    assert "rankingScore" not in results[0].model_dump()

    impression_payload = RecommendationImpressionRequest.model_validate(
        {
            "recommendationRequestId": request_id,
            "items": [{"targetType": "PROFILE", "targetId": candidate_id, "position": 1}],
            "occurredAt": datetime.now(UTC),
        }
    )
    recorded = store.record_recommendation_impressions(owner_id, impression_payload)
    assert recorded[0].duplicate is False
    duplicate = store.record_recommendation_impressions(owner_id, impression_payload)
    assert duplicate[0].duplicate is True
    assert_service_error(
        "IMPRESSION_CONFLICT",
        lambda: store.record_recommendation_impressions(
            owner_id,
            RecommendationImpressionRequest.model_validate(
                {
                    "recommendationRequestId": request_id,
                    "items": [RecommendationImpressionItem(targetType="PROFILE", targetId=candidate_id, position=2)],
                    "occurredAt": datetime.now(UTC),
                }
            ),
        ),
    )
    with sql_store[1]() as session:
        row = session.scalar(select(RecommendationImpressionRow).where(RecommendationImpressionRow.request_id == request_id))
        assert row is not None
        assert row.viewer_user_id == owner_id

    project_results, _, _ = store.user_project_matches(candidate_id, 20, None)
    assert [item.targetId for item in project_results] == [role_id]

    store.create_block(owner_id, candidate_id)
    blocked, _, _ = store.project_matches(owner_id, published.id, role_id, 20, None)
    assert blocked == []


def test_match_preferences_and_project_constraints_survive_recreation(sql_store) -> None:
    store, factory, engine = sql_store
    user_id, _, _ = store.login("wechat:app-a:matching-fields")
    preferences_payload = MatchPreferencesPayload.model_validate(
        {
            "desiredDirections": ["AI", "科研"],
            "availabilitySlots": [
                {"weekday": 6, "startMinute": 540, "endMinute": 720},
                {"weekday": 7, "startMinute": 780, "endMinute": 900},
            ],
        }
    )
    preferences = store.save_match_preferences(user_id, preferences_payload, 0)

    project_input = project_payload("结构化约束项目").model_dump()
    project_input["collaborationScenarios"] = ["竞赛", "科研"]
    project_input["roles"][0].update(
        {
            "skills": ["Python", "MySQL"],
            "requiredSkills": ["Python"],
            "requiredAvailabilitySlots": [
                {"weekday": 6, "startMinute": 540, "endMinute": 720}
            ],
            "collaborationRole": "MEMBER",
        }
    )
    project = store.create_project(user_id, ProjectPayload.model_validate(project_input))

    recreated = SqlAlchemyStore(factory, engine)
    assert recreated.get_match_preferences(user_id) == preferences
    assert recreated.get_project(project.id) == project

    legacy_update = project_payload("旧客户端更新").model_dump()
    legacy_update["roles"][0]["skills"] = ["Python", "MySQL"]
    updated = recreated.update_project(
        user_id,
        project.id,
        ProjectUpdate.model_validate({**legacy_update, "version": project.version}),
    )
    assert updated.collaborationScenarios == ["竞赛", "科研"]
    assert updated.roles[0].requiredSkills == ["Python"]
    assert updated.roles[0].requiredAvailabilitySlots[0].weekday == 6

    changed_skills = project_payload("移除必需技能").model_dump()
    changed_skills["roles"][0]["skills"] = ["MySQL"]
    removed = recreated.update_project(
        user_id,
        project.id,
        ProjectUpdate.model_validate({**changed_skills, "version": updated.version}),
    )
    assert removed.roles[0].requiredSkills == []


def test_project_member_state_capacity_permissions_and_persistence(sql_store) -> None:
    store, factory, engine = sql_store
    owner_id, _, _ = store.login("wechat:app-a:member-owner")
    first_user_id, _, _ = store.login("wechat:app-a:member-first")
    second_user_id, _, _ = store.login("wechat:app-a:member-second")
    outsider_id, _, _ = store.login("wechat:app-a:member-outsider")
    draft = store.create_project(owner_id, project_payload("成员项目"))
    role_id = draft.roles[0].id

    second_project = store.create_project(owner_id, project_payload("另一个项目"))
    second_project = store.publish_project(owner_id, second_project.id, second_project.version)
    assert_service_error(
        "RESOURCE_NOT_FOUND",
        lambda: store.add_project_member(second_project.id, role_id, first_user_id),
    )

    assert_service_error("PROJECT_NOT_MATCHABLE", lambda: store.add_project_member(draft.id, role_id, first_user_id))
    published = store.publish_project(owner_id, draft.id, draft.version)
    member = store.add_project_member(published.id, role_id, first_user_id)

    assert member.userId == first_user_id
    assert store.list_project_members(owner_id, published.id) == [member]
    assert store.list_project_members(first_user_id, published.id) == [member]
    assert_service_error("FORBIDDEN", lambda: store.list_project_members(outsider_id, published.id))
    assert_service_error(
        "MEMBER_ALREADY_EXISTS",
        lambda: store.add_project_member(published.id, role_id, first_user_id),
    )
    assert_service_error("ROLE_FULL", lambda: store.add_project_member(published.id, role_id, second_user_id))

    recreated = SqlAlchemyStore(factory, engine)
    assert recreated.list_project_members(owner_id, published.id) == [member]
    refreshed = recreated.get_project(published.id)
    assert refreshed.roles[0].filledCount == 1
    assert refreshed.roles[0].remainingCount == 0

    closed = recreated.close_project(owner_id, published.id, refreshed.version)
    assert recreated.list_project_members(owner_id, closed.id) == [member]
    assert_service_error("PROJECT_NOT_MATCHABLE", lambda: recreated.add_project_member(closed.id, role_id, second_user_id))


def test_closed_role_rejects_new_member(sql_store) -> None:
    store, _, _ = sql_store
    owner_id, _, _ = store.login("wechat:app-a:closed-role-owner")
    user_id, _, _ = store.login("wechat:app-a:closed-role-user")
    payload = project_payload("关闭岗位项目").model_dump()
    payload["roles"].append(
        {
            "name": "已关闭岗位",
            "skills": ["Python"],
            "headcount": 1,
            "hoursPerWeek": 8,
            "status": "CLOSED",
        }
    )
    draft = store.create_project(owner_id, ProjectPayload.model_validate(payload))
    published = store.publish_project(owner_id, draft.id, draft.version)

    assert_service_error(
        "ROLE_NOT_OPEN",
        lambda: store.add_project_member(published.id, published.roles[1].id, user_id),
    )


def test_blocks_are_bidirectional_and_prevent_new_members(sql_store) -> None:
    store, _, _ = sql_store
    owner_id, _, _ = store.login("wechat:app-a:block-owner")
    member_id, _, _ = store.login("wechat:app-a:block-member")
    project = store.create_project(owner_id, project_payload("拉黑成员项目"))
    published = store.publish_project(owner_id, project.id, project.version)
    block = store.create_block(owner_id, member_id)
    assert block.blockedUserId == member_id
    assert store.users_blocked(owner_id, member_id) is True
    assert store.users_blocked(member_id, owner_id) is True
    assert_service_error(
        "USER_BLOCKED",
        lambda: store.add_project_member(published.id, published.roles[0].id, member_id),
    )
    assert store.remove_block(owner_id, member_id) is True
    assert store.remove_block(owner_id, member_id) is False
    assert store.users_blocked(owner_id, member_id) is False
    assert store.add_project_member(published.id, published.roles[0].id, member_id).userId == member_id


def test_reports_persist_idempotently_and_enforce_message_visibility(sql_store) -> None:
    store, factory, engine = sql_store
    reporter_id, _, _ = store.login("wechat:app-a:reporter")
    target_id, _, _ = store.login("wechat:app-a:report-target")
    outsider_id, _, _ = store.login("wechat:app-a:report-outsider")
    user_report = ReportRequest(
        targetType="USER", targetId=target_id, reason="HARASSMENT", description="重复骚扰"
    )
    created = store.create_report(reporter_id, user_report, "req_report_1")
    assert store.create_report(reporter_id, user_report, "req_report_retry") == created
    recreated = SqlAlchemyStore(factory, engine)
    assert recreated.create_report(reporter_id, user_report, "req_report_recreated") == created
    with factory() as session:
        report_events = list(
            session.scalars(select(AuditEventRow).where(AuditEventRow.resource_id == created.id))
        )
        assert len(report_events) == 1
        assert report_events[0].request_id == "req_report_1"
        assert report_events[0].action == "REPORT_SUBMITTED"
    assert_service_error(
        "RESOURCE_NOT_FOUND",
        lambda: recreated.create_report(
            target_id, user_report.model_copy(update={"targetId": target_id}), "req_report_self"
        ),
    )

    project = recreated.create_project(target_id, project_payload("举报消息项目"))
    published = recreated.publish_project(target_id, project.id, project.version)
    conversation = recreated.create_conversation(reporter_id, published.id, target_id)
    message = recreated.send_message(target_id, conversation.id, "report-message-1", "不合适的消息")
    message_report = ReportRequest(
        targetType="MESSAGE", targetId=message.id, reason="INAPPROPRIATE_CONTENT", description=""
    )
    assert recreated.create_report(reporter_id, message_report, "req_report_message").targetId == message.id
    assert_service_error(
        "RESOURCE_NOT_FOUND",
        lambda: recreated.create_report(outsider_id, message_report, "req_report_outsider"),
    )
    recreated.request_account_deletion(target_id, "req_report_target_deletion")
    assert recreated.create_report(reporter_id, user_report, "req_report_after_deletion") == created


def test_account_deletion_request_persists_and_revokes_all_sessions(sql_store) -> None:
    store, factory, engine = sql_store
    user_id, first_token, _ = store.login("wechat:app-a:delete-account")
    same_user_id, second_token, _ = store.login("wechat:app-a:delete-account")
    assert same_user_id == user_id
    request_data = store.request_account_deletion(user_id, "req_delete_1")
    assert request_data.status == "PENDING"
    assert_service_error("SESSION_EXPIRED", lambda: store.user_for_token(first_token))
    assert_service_error("SESSION_EXPIRED", lambda: store.user_for_token(second_token))
    assert_service_error("FORBIDDEN", lambda: store.login("wechat:app-a:delete-account"))
    recreated = SqlAlchemyStore(factory, engine)
    assert recreated.request_account_deletion(user_id, "req_delete_retry") == request_data
    with factory() as session:
        user = session.get(UserRow, user_id)
        row = session.get(AccountDeletionRequestRow, request_data.id)
        assert user is not None and user.status == "DELETION_PENDING"
        assert row is not None and row.pending_user_id == user_id
        audit = session.scalar(
            select(AuditEventRow).where(AuditEventRow.resource_id == request_data.id)
        )
        assert audit is not None
        assert audit.request_id == "req_delete_1"
        assert audit.action == "ACCOUNT_DELETION_REQUESTED"


def test_invitations_persist_accept_reject_expire_and_enforce_permissions(sql_store) -> None:
    store, factory, engine = sql_store
    owner_id, _, _ = store.login("wechat:app-a:invitation-owner")
    invitee_id, _, _ = store.login("wechat:app-a:invitation-user")
    outsider_id, _, _ = store.login("wechat:app-a:invitation-outsider")
    second_id, _, _ = store.login("wechat:app-a:invitation-second")
    draft = store.create_project(owner_id, project_payload("邀请项目"))
    published = store.publish_project(owner_id, draft.id, draft.version)
    role_id = published.roles[0].id

    invitation = store.create_invitation(owner_id, published.id, role_id, invitee_id)
    assert store.create_invitation(owner_id, published.id, role_id, invitee_id) == invitation
    recreated = SqlAlchemyStore(factory, engine)
    assert_service_error(
        "RESOURCE_NOT_FOUND",
        lambda: recreated.accept_invitation(outsider_id, invitation.id),
    )
    accepted = recreated.accept_invitation(invitee_id, invitation.id)
    assert accepted.invitation.status == "ACCEPTED"
    assert accepted.member.userId == invitee_id
    assert recreated.accept_invitation(invitee_id, invitation.id) == accepted

    second_project = recreated.create_project(owner_id, project_payload("拒绝邀请项目"))
    second_project = recreated.publish_project(owner_id, second_project.id, second_project.version)
    rejected_invitation = recreated.create_invitation(
        owner_id, second_project.id, second_project.roles[0].id, second_id
    )
    rejected = recreated.reject_invitation(second_id, rejected_invitation.id)
    assert rejected.status == "REJECTED"
    assert recreated.reject_invitation(second_id, rejected_invitation.id) == rejected
    assert_service_error(
        "INVITATION_NOT_ACTIONABLE",
        lambda: recreated.accept_invitation(second_id, rejected_invitation.id),
    )

    expiring_project = recreated.create_project(owner_id, project_payload("过期邀请项目"))
    expiring_project = recreated.publish_project(owner_id, expiring_project.id, expiring_project.version)
    expiring = recreated.create_invitation(
        owner_id, expiring_project.id, expiring_project.roles[0].id, second_id
    )
    with factory.begin() as session:
        row = session.get(InvitationRow, expiring.id)
        assert row is not None
        row.expires_at = db_now() - timedelta(seconds=1)
    assert_service_error(
        "INVITATION_NOT_ACTIONABLE",
        lambda: recreated.accept_invitation(second_id, expiring.id),
    )
    replacement = recreated.create_invitation(
        owner_id, expiring_project.id, expiring_project.roles[0].id, second_id
    )
    assert replacement.id != expiring.id

    closed_project = recreated.create_project(owner_id, project_payload("关闭邀请项目"))
    closed_project = recreated.publish_project(owner_id, closed_project.id, closed_project.version)
    closing = recreated.create_invitation(
        owner_id, closed_project.id, closed_project.roles[0].id, second_id
    )
    recreated.close_project(owner_id, closed_project.id, closed_project.version)
    assert_service_error(
        "PROJECT_NOT_MATCHABLE",
        lambda: recreated.accept_invitation(second_id, closing.id),
    )


def test_conversations_messages_persist_page_and_enforce_privacy(sql_store) -> None:
    store, factory, engine = sql_store
    owner_id, _, _ = store.login("wechat:app-a:conversation-owner")
    other_id, _, _ = store.login("wechat:app-a:conversation-other")
    outsider_id, _, _ = store.login("wechat:app-a:conversation-outsider")
    unrelated_id, _, _ = store.login("wechat:app-a:conversation-unrelated")
    draft = store.create_project(owner_id, project_payload("会话项目"))
    published = store.publish_project(owner_id, draft.id, draft.version)

    conversation = store.create_conversation(other_id, published.id, owner_id)
    assert store.create_conversation(owner_id, published.id, other_id) == conversation
    assert_service_error(
        "FORBIDDEN",
        lambda: store.create_conversation(outsider_id, published.id, unrelated_id),
    )
    assert_service_error(
        "RESOURCE_NOT_FOUND",
        lambda: store.list_messages(outsider_id, conversation.id, 20, None),
    )

    first = store.send_message(other_id, conversation.id, "device-001", "第一条")
    second = store.send_message(owner_id, conversation.id, "device-001", "第二条")
    third = store.send_message(other_id, conversation.id, "device-002", "第三条")
    assert store.send_message(other_id, conversation.id, "device-001", "第一条") == first
    assert_service_error(
        "MESSAGE_IDEMPOTENCY_CONFLICT",
        lambda: store.send_message(other_id, conversation.id, "device-001", "不同正文"),
    )
    first_page, cursor = store.list_messages(owner_id, conversation.id, 2, None)
    second_page, next_cursor = store.list_messages(owner_id, conversation.id, 2, cursor)
    expected_messages = sorted([first, second, third], key=lambda item: (item.createdAt, item.id))
    assert first_page == expected_messages[:2]
    assert second_page == expected_messages[2:]
    assert cursor is not None
    assert next_cursor is None

    recreated = SqlAlchemyStore(factory, engine)
    conversations, conversation_cursor = recreated.list_conversations(other_id, 20, None)
    assert conversations[0].id == conversation.id
    assert conversations[0].lastMessageAt == third.createdAt
    assert conversation_cursor is None
    assert recreated.list_messages(other_id, conversation.id, 20, None)[0] == expected_messages

    additional_conversations = []
    for index in range(2):
        extra_project = recreated.create_project(owner_id, project_payload(f"分页会话项目 {index}"))
        extra_project = recreated.publish_project(owner_id, extra_project.id, extra_project.version)
        additional_conversations.append(
            recreated.create_conversation(owner_id, extra_project.id, other_id)
        )
    conversation_page, conversation_cursor = recreated.list_conversations(owner_id, 2, None)
    remaining_page, final_cursor = recreated.list_conversations(owner_id, 2, conversation_cursor)
    assert len(conversation_page) == 2
    assert len(remaining_page) == 1
    assert {item.id for item in conversation_page + remaining_page} == {
        conversation.id,
        *(item.id for item in additional_conversations),
    }
    assert conversation_cursor is not None
    assert final_cursor is None

    recreated.create_block(other_id, owner_id)
    assert_service_error(
        "USER_BLOCKED",
        lambda: recreated.send_message(owner_id, conversation.id, "blocked-001", "不能发送"),
    )
    assert recreated.list_messages(owner_id, conversation.id, 20, None)[0] == expected_messages
