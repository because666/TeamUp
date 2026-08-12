from fastapi.testclient import TestClient

from app.config import Settings
from app.main import make_app
from app.store import MemoryStore


def make_client() -> TestClient:
    return TestClient(make_app(Settings(environment="test", allow_local_login=True)))


def login(client: TestClient, subject: str = "alice") -> str:
    response = client.post("/api/v1/auth/wechat/login", json={"code": f"local:{subject}", "consentAccepted": True})
    assert response.status_code == 200
    return response.json()["data"]["accessToken"]


def profile_payload() -> dict:
    return {
        "nickname": "林同学",
        "school": "示例大学",
        "major": "计算机科学",
        "grade": "大三",
        "skills": ["Python"],
        "collaborationScenarios": ["竞赛"],
        "rolePreference": "FLEXIBLE",
        "hoursPerWeek": 8,
        "bio": "负责后端开发",
        "visibility": True,
        "version": 0,
    }


def project_payload() -> dict:
    return {
        "title": "校园创新项目",
        "description": "为学生提供协作工具",
        "direction": "AI",
        "competition": "互联网+",
        "stage": "IDEA",
        "teamInfo": "已有产品同学",
        "roles": [{"name": "后端开发", "skills": ["Python"], "headcount": 1, "hoursPerWeek": 8, "description": "", "status": "OPEN"}],
    }


def test_health_and_request_id() -> None:
    client = make_client()
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "req_test"})
    assert response.status_code == 200
    assert response.json()["requestId"] == "req_test"
    assert response.headers["X-Request-ID"] == "req_test"


def test_openapi_has_typed_responses_and_production_rejects_memory() -> None:
    app = make_app(Settings(environment="test", allow_local_login=True))
    schema = app.openapi()
    response_schema = schema["paths"]["/api/v1/me/profile"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert "$ref" in response_schema
    try:
        make_app(Settings(environment="production", store_backend="memory", allow_local_login=False))
    except RuntimeError as error:
        assert "memory store" in str(error)
    else:
        raise AssertionError("production must reject the memory store")


def test_vertical_profile_and_project_flow() -> None:
    client = make_client()
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/me/profile", headers=headers).json()["data"] is None
    saved_profile = client.put("/api/v1/me/profile", headers=headers, json=profile_payload())
    assert saved_profile.status_code == 200
    assert saved_profile.json()["data"]["version"] == 1

    project = client.post("/api/v1/projects", headers=headers, json=project_payload())
    assert project.status_code == 200
    project_data = project.json()["data"]
    assert project_data["status"] == "DRAFT"

    published = client.post(
        f"/api/v1/projects/{project_data['id']}/publish",
        headers=headers,
        json={"version": project_data["version"]},
    )
    assert published.status_code == 200
    assert published.json()["data"]["status"] == "PUBLISHED"


def test_auth_and_version_boundaries() -> None:
    client = make_client()
    assert client.get("/api/v1/me/profile").status_code == 401
    assert client.post("/api/v1/auth/wechat/login", json={"code": "local:a", "consentAccepted": False}).status_code == 422

    token = login(client, "owner")
    headers = {"Authorization": f"Bearer {token}"}
    profile = client.put("/api/v1/me/profile", headers=headers, json=profile_payload())
    assert profile.status_code == 200
    stale = profile_payload()
    stale["version"] = 0
    assert client.put("/api/v1/me/profile", headers=headers, json=stale).status_code == 409


def test_project_owner_is_enforced() -> None:
    client = make_client()
    owner_token = login(client, "owner")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    project = client.post("/api/v1/projects", headers=owner_headers, json=project_payload()).json()["data"]

    other_token = login(client, "other")
    response = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={**project_payload(), "version": project["version"]},
    )
    assert response.status_code == 403


def test_match_preferences_auth_validation_and_versioning() -> None:
    client = make_client()
    path = "/api/v1/me/match-preferences"
    assert client.get(path).status_code == 401

    token = login(client, "preferences")
    headers = {"Authorization": f"Bearer {token}"}
    empty = client.get(path, headers=headers)
    assert empty.status_code == 200
    assert empty.json()["data"] is None
    assert empty.json()["meta"]["state"] == "INCOMPLETE"

    payload = {
        "desiredDirections": ["AI", "校园服务"],
        "availabilitySlots": [
            {"timezone": "Asia/Shanghai", "weekday": 6, "startMinute": 540, "endMinute": 720},
            {"timezone": "Asia/Shanghai", "weekday": 7, "startMinute": 780, "endMinute": 900},
        ],
        "version": 0,
    }
    created = client.put(path, headers=headers, json=payload)
    assert created.status_code == 200
    assert created.json()["data"]["version"] == 1
    assert client.get(path, headers=headers).json()["data"]["desiredDirections"] == ["AI", "校园服务"]

    updated_payload = {**payload, "desiredDirections": ["科研"], "version": 1}
    updated = client.put(path, headers=headers, json=updated_payload)
    assert updated.status_code == 200
    assert updated.json()["data"]["version"] == 2
    assert client.put(path, headers=headers, json=updated_payload).status_code == 409

    duplicate = {**payload, "desiredDirections": ["AI", " ai "]}
    assert client.put(path, headers=headers, json=duplicate).status_code == 422
    nested_overlap = {
        **payload,
        "availabilitySlots": [
            {"weekday": 1, "startMinute": 480, "endMinute": 720},
            {"weekday": 1, "startMinute": 500, "endMinute": 540},
            {"weekday": 1, "startMinute": 600, "endMinute": 660},
        ],
    }
    assert client.put(path, headers=headers, json=nested_overlap).status_code == 422


def test_project_matching_fields_and_legacy_update_compatibility() -> None:
    client = make_client()
    token = login(client, "project-fields")
    headers = {"Authorization": f"Bearer {token}"}
    payload = project_payload()
    payload["collaborationScenarios"] = ["竞赛", "科研"]
    payload["roles"][0].update(
        {
            "requiredSkills": ["Python"],
            "requiredAvailabilitySlots": [
                {"weekday": 6, "startMinute": 540, "endMinute": 720}
            ],
            "collaborationRole": "MEMBER",
        }
    )
    created = client.post("/api/v1/projects", headers=headers, json=payload)
    assert created.status_code == 200
    project = created.json()["data"]
    assert project["collaborationScenarios"] == ["竞赛", "科研"]
    assert project["roles"][0]["requiredSkills"] == ["Python"]
    assert project["roles"][0]["requiredAvailabilitySlots"][0]["weekday"] == 6

    legacy_payload = {**project_payload(), "title": "旧客户端更新", "version": project["version"]}
    updated = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers=headers,
        json=legacy_payload,
    )
    assert updated.status_code == 200
    updated_data = updated.json()["data"]
    assert updated_data["collaborationScenarios"] == ["竞赛", "科研"]
    assert updated_data["roles"][0]["requiredSkills"] == ["Python"]
    assert updated_data["roles"][0]["requiredAvailabilitySlots"][0]["weekday"] == 6

    invalid = project_payload()
    invalid["roles"][0]["requiredSkills"] = ["Go"]
    assert client.post("/api/v1/projects", headers=headers, json=invalid).status_code == 422


def test_project_member_list_permissions_and_capacity() -> None:
    store = MemoryStore()
    client = TestClient(make_app(Settings(environment="test", allow_local_login=True), store_override=store))
    owner_token = login(client, "member-owner")
    member_token = login(client, "member-user")
    outsider_token = login(client, "member-outsider")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    project = client.post("/api/v1/projects", headers=owner_headers, json=project_payload()).json()["data"]
    published = client.post(
        f"/api/v1/projects/{project['id']}/publish",
        headers=owner_headers,
        json={"version": project["version"]},
    ).json()["data"]
    role_id = published["roles"][0]["id"]

    member_user_id = store.user_for_token(member_token)
    store.add_project_member(project["id"], role_id, member_user_id)
    path = f"/api/v1/projects/{project['id']}/members"

    assert client.get(path).status_code == 401
    assert client.get(path, headers={"Authorization": f"Bearer {outsider_token}"}).status_code == 403
    owner_view = client.get(path, headers=owner_headers)
    member_view = client.get(path, headers={"Authorization": f"Bearer {member_token}"})
    assert owner_view.status_code == 200
    assert member_view.status_code == 200
    assert owner_view.json()["data"][0]["userId"] == member_user_id
    assert owner_view.json()["data"][0]["roleName"] == "后端开发"

    refreshed = client.get(f"/api/v1/projects/{project['id']}", headers=owner_headers).json()["data"]
    assert refreshed["roles"][0]["filledCount"] == 1
    assert refreshed["roles"][0]["remainingCount"] == 0


def test_blocks_are_idempotent_private_and_remove_cleanly() -> None:
    store = MemoryStore()
    client = TestClient(make_app(Settings(environment="test", allow_local_login=True), store_override=store))
    blocker_token = login(client, "blocker")
    blocked_token = login(client, "blocked")
    blocker_id = store.user_for_token(blocker_token)
    blocked_id = store.user_for_token(blocked_token)
    headers = {"Authorization": f"Bearer {blocker_token}"}

    self_response = client.post("/api/v1/blocks", headers=headers, json={"blockedUserId": blocker_id})
    assert self_response.status_code == 422
    created = client.post("/api/v1/blocks", headers=headers, json={"blockedUserId": blocked_id})
    assert created.status_code == 200
    assert created.json()["data"]["blockedUserId"] == blocked_id
    repeated = client.post("/api/v1/blocks", headers=headers, json={"blockedUserId": blocked_id})
    assert repeated.status_code == 200
    assert repeated.json()["data"] == created.json()["data"]
    assert store.users_blocked(blocker_id, blocked_id) is True

    removed = client.delete(f"/api/v1/blocks/{blocked_id}", headers=headers)
    assert removed.status_code == 200
    assert removed.json()["data"] == {"blockedUserId": blocked_id, "removed": True}
    repeated_remove = client.delete(f"/api/v1/blocks/{blocked_id}", headers=headers)
    assert repeated_remove.status_code == 200
    assert repeated_remove.json()["data"]["removed"] is False
    assert store.users_blocked(blocker_id, blocked_id) is False

    assert client.post("/api/v1/blocks", headers=headers, json={"blockedUserId": "usr_missing"}).status_code == 404
    assert client.post("/api/v1/blocks", json={"blockedUserId": blocked_id}).status_code == 401

    schema = client.app.openapi()
    assert "post" in schema["paths"]["/api/v1/blocks"]
    assert "delete" in schema["paths"]["/api/v1/blocks/{blocked_user_id}"]


def test_delete_block_cors_preflight() -> None:
    client = make_client()
    response = client.options(
        "/api/v1/blocks/usr_target",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert response.status_code == 200
    assert "DELETE" in response.headers["access-control-allow-methods"]


def test_invitation_create_accept_permissions_and_idempotency() -> None:
    store = MemoryStore()
    client = TestClient(make_app(Settings(environment="test", allow_local_login=True), store_override=store))
    owner_token = login(client, "invite-owner")
    invitee_token = login(client, "invite-user")
    outsider_token = login(client, "invite-outsider")
    owner_id = store.user_for_token(owner_token)
    invitee_id = store.user_for_token(invitee_token)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    invitee_headers = {"Authorization": f"Bearer {invitee_token}"}
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}
    draft = client.post("/api/v1/projects", headers=owner_headers, json=project_payload()).json()["data"]
    role_id = draft["roles"][0]["id"]
    payload = {"projectId": draft["id"], "roleId": role_id, "inviteeUserId": invitee_id}

    assert client.post("/api/v1/invitations", json=payload).status_code == 401
    assert client.post("/api/v1/invitations", headers=owner_headers, json=payload).status_code == 409
    published = client.post(
        f"/api/v1/projects/{draft['id']}/publish",
        headers=owner_headers,
        json={"version": draft["version"]},
    ).json()["data"]
    payload["roleId"] = published["roles"][0]["id"]
    assert client.post("/api/v1/invitations", headers=outsider_headers, json=payload).status_code == 403
    self_payload = {**payload, "inviteeUserId": owner_id}
    assert client.post("/api/v1/invitations", headers=owner_headers, json=self_payload).status_code == 422

    created = client.post("/api/v1/invitations", headers=owner_headers, json=payload)
    assert created.status_code == 200
    invitation = created.json()["data"]
    assert invitation["status"] == "PENDING"
    assert invitation["inviteeUserId"] == invitee_id
    repeated = client.post("/api/v1/invitations", headers=owner_headers, json=payload)
    assert repeated.status_code == 200
    assert repeated.json()["data"] == invitation

    accept_path = f"/api/v1/invitations/{invitation['id']}/accept"
    assert client.post(accept_path).status_code == 401
    assert client.post(accept_path, headers=outsider_headers).status_code == 404
    accepted = client.post(accept_path, headers=invitee_headers)
    assert accepted.status_code == 200
    accepted_data = accepted.json()["data"]
    assert accepted_data["invitation"]["status"] == "ACCEPTED"
    assert accepted_data["member"]["userId"] == invitee_id
    assert client.post(accept_path, headers=invitee_headers).json()["data"] == accepted_data
    assert len(store.project_members) == 1

    schema = client.app.openapi()
    assert "post" in schema["paths"]["/api/v1/invitations"]
    assert "post" in schema["paths"]["/api/v1/invitations/{invitation_id}/accept"]
    assert "post" in schema["paths"]["/api/v1/invitations/{invitation_id}/reject"]


def test_invitation_reject_expiry_block_and_capacity_boundaries() -> None:
    store = MemoryStore()
    client = TestClient(make_app(Settings(environment="test", allow_local_login=True), store_override=store))
    owner_token = login(client, "reject-owner")
    invitee_token = login(client, "reject-user")
    second_token = login(client, "reject-second")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    invitee_headers = {"Authorization": f"Bearer {invitee_token}"}
    owner_id = store.user_for_token(owner_token)
    invitee_id = store.user_for_token(invitee_token)
    second_id = store.user_for_token(second_token)
    draft = client.post("/api/v1/projects", headers=owner_headers, json=project_payload()).json()["data"]
    published = client.post(
        f"/api/v1/projects/{draft['id']}/publish",
        headers=owner_headers,
        json={"version": draft["version"]},
    ).json()["data"]
    role_id = published["roles"][0]["id"]
    payload = {"projectId": published["id"], "roleId": role_id, "inviteeUserId": invitee_id}

    store.create_block(invitee_id, owner_id)
    assert client.post("/api/v1/invitations", headers=owner_headers, json=payload).status_code == 409
    store.remove_block(invitee_id, owner_id)
    invitation = client.post("/api/v1/invitations", headers=owner_headers, json=payload).json()["data"]
    reject_path = f"/api/v1/invitations/{invitation['id']}/reject"
    rejected = client.post(reject_path, headers=invitee_headers)
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "REJECTED"
    assert client.post(reject_path, headers=invitee_headers).json()["data"] == rejected.json()["data"]
    assert client.post(f"/api/v1/invitations/{invitation['id']}/accept", headers=invitee_headers).status_code == 409

    second_payload = {**payload, "inviteeUserId": second_id}
    expiring = client.post("/api/v1/invitations", headers=owner_headers, json=second_payload).json()["data"]
    stored = store.invitations[expiring["id"]]
    store.invitations[expiring["id"]] = stored.model_copy(update={"expiresAt": stored.createdAt})
    second_headers = {"Authorization": f"Bearer {second_token}"}
    assert client.post(f"/api/v1/invitations/{expiring['id']}/accept", headers=second_headers).status_code == 409
    replacement = client.post("/api/v1/invitations", headers=owner_headers, json=second_payload)
    assert replacement.status_code == 200
    assert replacement.json()["data"]["id"] != expiring["id"]

    store.add_project_member(published["id"], role_id, invitee_id)
    assert client.post("/api/v1/invitations", headers=owner_headers, json=second_payload).status_code == 409


def test_conversation_message_flow_permissions_idempotency_and_blocking() -> None:
    store = MemoryStore()
    client = TestClient(make_app(Settings(environment="test", allow_local_login=True), store_override=store))
    owner_token = login(client, "message-owner")
    other_token = login(client, "message-other")
    outsider_token = login(client, "message-outsider")
    owner_id = store.user_for_token(owner_token)
    other_id = store.user_for_token(other_token)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}
    draft = client.post("/api/v1/projects", headers=owner_headers, json=project_payload()).json()["data"]
    published = client.post(
        f"/api/v1/projects/{draft['id']}/publish",
        headers=owner_headers,
        json={"version": draft["version"]},
    ).json()["data"]
    payload = {"projectId": published["id"], "otherUserId": owner_id}

    assert client.post("/api/v1/conversations", json=payload).status_code == 401
    created = client.post("/api/v1/conversations", headers=other_headers, json=payload)
    assert created.status_code == 200
    conversation = created.json()["data"]
    assert conversation["participantUserIds"] == sorted([owner_id, other_id])
    assert client.post("/api/v1/conversations", headers=owner_headers, json={"projectId": published["id"], "otherUserId": other_id}).json()["data"] == conversation
    assert client.post("/api/v1/conversations", headers=owner_headers, json={"projectId": published["id"], "otherUserId": owner_id}).status_code == 422

    message_path = f"/api/v1/conversations/{conversation['id']}/messages"
    message_payload = {"clientMessageId": "mobile-001", "content": "  你好，想了解项目  "}
    assert client.post(message_path, json=message_payload).status_code == 401
    assert client.post(message_path, headers=outsider_headers, json=message_payload).status_code == 404
    sent = client.post(message_path, headers=other_headers, json=message_payload)
    assert sent.status_code == 200
    message = sent.json()["data"]
    assert message["content"] == "你好，想了解项目"
    assert client.post(message_path, headers=other_headers, json={**message_payload, "content": "你好，想了解项目"}).json()["data"] == message
    conflict = client.post(message_path, headers=other_headers, json={**message_payload, "content": "不同内容"})
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "MESSAGE_IDEMPOTENCY_CONFLICT"
    assert client.post(message_path, headers=other_headers, json={"clientMessageId": "blank", "content": "   "}).status_code == 422
    assert client.post(message_path, headers=other_headers, json={"clientMessageId": "long", "content": "中" * 1001}).status_code == 422

    store.create_block(owner_id, other_id)
    assert client.post(message_path, headers=owner_headers, json={"clientMessageId": "blocked", "content": "新消息"}).status_code == 409
    history = client.get(message_path, headers=owner_headers)
    assert history.status_code == 200
    assert history.json()["data"] == [message]
    assert client.get(message_path, headers=outsider_headers).status_code == 404
    assert client.get(message_path, headers=owner_headers, params={"cursor": "invalid"}).status_code == 422
    assert client.get("/api/v1/conversations", headers=owner_headers).json()["data"][0]["id"] == conversation["id"]
    assert client.get("/api/v1/conversations", headers=owner_headers, params={"cursor": "invalid"}).status_code == 422

    schema = client.app.openapi()
    assert "post" in schema["paths"]["/api/v1/conversations"]
    assert "get" in schema["paths"]["/api/v1/conversations"]
    assert {"get", "post"}.issubset(schema["paths"]["/api/v1/conversations/{conversation_id}/messages"])
