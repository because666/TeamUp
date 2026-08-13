from datetime import UTC, datetime

import logging

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import make_app
from app.rate_limit import InMemoryRateLimiter, RateLimitRule
from app.store import MemoryStore


def make_client(rate_limiter: InMemoryRateLimiter | None = None) -> TestClient:
    return TestClient(make_app(Settings(environment="test", allow_local_login=True), rate_limiter=rate_limiter))


def test_rate_limiter_returns_retry_after_for_login_burst() -> None:
    limiter = InMemoryRateLimiter({"auth.login": RateLimitRule(window_seconds=60, max_requests=2)})
    client = make_client(limiter)
    assert client.post("/api/v1/auth/wechat/login", json={"code": "local:limit-a", "consentAccepted": True}).status_code == 200
    assert client.post("/api/v1/auth/wechat/login", json={"code": "local:limit-b", "consentAccepted": True}).status_code == 200
    response = client.post("/api/v1/auth/wechat/login", json={"code": "local:limit-c", "consentAccepted": True})
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"
    assert int(response.headers["Retry-After"]) >= 1


def test_rate_limiter_resets_at_window_boundary() -> None:
    limiter = InMemoryRateLimiter({"test": RateLimitRule(window_seconds=10, max_requests=1)})
    assert limiter.check("test", "subject", now=10.0) is None
    assert limiter.check("test", "subject", now=10.5) is not None
    assert limiter.check("test", "subject", now=20.0) is None


def test_rate_limiter_prunes_expired_keys_without_affecting_active_windows() -> None:
    limiter = InMemoryRateLimiter({"test": RateLimitRule(window_seconds=10, max_requests=2)})
    assert limiter.check("test", "expired", now=10.0) is None
    assert limiter.check("test", "active", now=10.0) is None
    assert limiter.check("test", "active", now=10.5) is None
    assert limiter.check("test", "active", now=10.6) is not None
    assert limiter.check("test", "new", now=20.0) is None
    assert ("test", "expired") not in limiter._windows
    assert ("test", "active") not in limiter._windows


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


def test_unexpected_store_exception_is_redacted() -> None:
    class BrokenStore(MemoryStore):
        def ready(self) -> bool:
            raise RuntimeError("database password=should-not-leak")

    client = TestClient(
        make_app(Settings(environment="test", allow_local_login=True), store_override=BrokenStore()),
        raise_server_exceptions=False,
    )
    response = client.get("/api/v1/health/ready", headers={"X-Request-ID": "req_internal"})
    assert response.status_code == 503
    assert response.json() == {
            "error": {
                "code": "DEPENDENCY_NOT_READY",
                "message": "必要依赖尚未就绪。",
                "details": [],
        },
        "requestId": "req_internal",
    }
    assert "should-not-leak" not in response.text


def test_health_ready_maps_store_failure_to_dependency_not_ready() -> None:
    class UnavailableStore(MemoryStore):
        def ready(self) -> bool:
            raise RuntimeError("connection refused")

    client = TestClient(make_app(Settings(environment="test", allow_local_login=True), store_override=UnavailableStore()))
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DEPENDENCY_NOT_READY"
    assert "connection refused" not in response.text


def test_logout_records_audit_without_token() -> None:
    store = MemoryStore()
    client = TestClient(make_app(Settings(environment="test", allow_local_login=True), store_override=store))
    token = login(client, "logout-audit")
    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}", "X-Request-ID": "req_logout"})
    assert response.status_code == 200
    events = [event for event in store.audit_events if event["action"] == "LOGOUT"]
    assert len(events) == 1
    assert events[0]["requestId"] == "req_logout"
    assert events[0]["resourceType"] == "SESSION"
    assert token not in str(events[0])


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


def test_openapi_contract_has_all_public_routes_and_typed_success_responses() -> None:
    schema = make_app(Settings(environment="test", allow_local_login=True)).openapi()
    expected_operations = {
        ("get", "/api/v1/health/live"),
        ("get", "/api/v1/health/ready"),
        ("post", "/api/v1/auth/wechat/login"),
        ("post", "/api/v1/auth/logout"),
        ("post", "/api/v1/account/deletion-requests"),
        ("post", "/api/v1/blocks"),
        ("delete", "/api/v1/blocks/{blocked_user_id}"),
        ("post", "/api/v1/reports"),
        ("post", "/api/v1/invitations"),
        ("post", "/api/v1/invitations/{invitation_id}/accept"),
        ("post", "/api/v1/invitations/{invitation_id}/reject"),
        ("post", "/api/v1/conversations"),
        ("get", "/api/v1/conversations"),
        ("get", "/api/v1/conversations/{conversation_id}/messages"),
        ("post", "/api/v1/conversations/{conversation_id}/messages"),
        ("get", "/api/v1/me/profile"),
        ("put", "/api/v1/me/profile"),
        ("get", "/api/v1/profiles/{profile_id}"),
        ("get", "/api/v1/profiles"),
        ("get", "/api/v1/me/match-preferences"),
        ("put", "/api/v1/me/match-preferences"),
        ("get", "/api/v1/projects/{project_id}/matches"),
        ("get", "/api/v1/me/project-matches"),
        ("post", "/api/v1/recommendation-impressions"),
        ("post", "/api/v1/projects"),
        ("get", "/api/v1/projects/{project_id}"),
        ("get", "/api/v1/projects/{project_id}/members"),
        ("patch", "/api/v1/projects/{project_id}"),
        ("post", "/api/v1/projects/{project_id}/publish"),
        ("post", "/api/v1/projects/{project_id}/close"),
        ("get", "/api/v1/projects"),
        ("get", "/api/v1/me/projects"),
    }
    actual_operations = {
        (method, path)
        for path, methods in schema["paths"].items()
        for method, operation in methods.items()
        if isinstance(operation, dict) and "responses" in operation
    }
    assert actual_operations == expected_operations
    for path, methods in schema["paths"].items():
        for operation in methods.values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            success = next((value for code, value in operation["responses"].items() if str(code).startswith("2")), None)
            assert success is not None, path
            response_schema = success.get("content", {}).get("application/json", {}).get("schema")
            assert response_schema, path


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


def test_discovery_filters_visibility_blocks_and_owner_projects() -> None:
    client = make_client()
    owner_token = login(client, "discovery-owner")
    candidate_token = login(client, "discovery-candidate")
    hidden_token = login(client, "discovery-hidden")
    viewer_token = login(client, "discovery-viewer")
    viewer_user_id = client.post(
        "/api/v1/auth/wechat/login", json={"code": "local:discovery-viewer", "consentAccepted": True}
    ).json()["data"]["userId"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    hidden_headers = {"Authorization": f"Bearer {hidden_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    candidate_login = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "local:discovery-candidate", "consentAccepted": True},
    ).json()["data"]
    hidden_login = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "local:discovery-hidden", "consentAccepted": True},
    ).json()["data"]

    assert client.put("/api/v1/me/profile", headers=candidate_headers, json=profile_payload()).status_code == 200
    hidden_profile = profile_payload()
    hidden_profile["nickname"] = "不公开用户"
    hidden_profile["visibility"] = False
    assert client.put("/api/v1/me/profile", headers=hidden_headers, json=hidden_profile).status_code == 200
    assert client.put(
        "/api/v1/me/match-preferences",
        headers=candidate_headers,
        json={"desiredDirections": ["AI"], "availabilitySlots": [], "version": 0},
    ).status_code == 200

    project = client.post("/api/v1/projects", headers=owner_headers, json=project_payload()).json()["data"]
    assert client.post(
        f"/api/v1/projects/{project['id']}/publish",
        headers=owner_headers,
        json={"version": project["version"]},
    ).status_code == 200

    projects = client.get(
        "/api/v1/projects?direction=ai&competition=%E4%BA%92%E8%81%94%E7%BD%91%2B&stage=idea&skill=python",
        headers=viewer_headers,
    )
    assert projects.status_code == 200
    assert [item["id"] for item in projects.json()["data"]] == [project["id"]]
    assert client.post(
        "/api/v1/blocks", headers=owner_headers, json={"blockedUserId": viewer_user_id}
    ).status_code == 200
    assert client.get("/api/v1/projects", headers=viewer_headers).json()["data"] == []
    assert client.get(
        f"/api/v1/projects/{project['id']}", headers=viewer_headers
    ).status_code == 404

    talent = client.get(
        "/api/v1/profiles?skill=python&direction=ai&collaborationRole=FLEXIBLE&minHoursPerWeek=6&maxHoursPerWeek=10",
        headers=viewer_headers,
    )
    assert talent.status_code == 200
    assert [item["id"] for item in talent.json()["data"]] == [candidate_login["userId"]]
    assert "version" not in talent.json()["data"][0]
    assert client.get(f"/api/v1/profiles/{hidden_login['userId']}", headers=viewer_headers).status_code == 404

    assert client.post(
        "/api/v1/blocks", headers=candidate_headers, json={"blockedUserId": viewer_user_id}
    ).status_code == 200
    assert client.get(f"/api/v1/profiles/{candidate_login['userId']}", headers=viewer_headers).status_code == 404
    assert client.get("/api/v1/profiles", headers=viewer_headers).json()["data"] == []

    mine = client.get("/api/v1/me/projects?status=PUBLISHED", headers=owner_headers)
    assert mine.status_code == 200
    assert [item["id"] for item in mine.json()["data"]] == [project["id"]]
    assert client.get("/api/v1/profiles").status_code == 401


def test_rule_matching_api_enforces_owner_visibility_constraints_and_cursor() -> None:
    client = make_client()
    owner_token = login(client, "match-owner")
    candidate_token = login(client, "match-candidate")
    incomplete_token = login(client, "match-incomplete")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    incomplete_headers = {"Authorization": f"Bearer {incomplete_token}"}

    candidate_profile = profile_payload()
    candidate_profile["skills"] = ["Python", "MySQL"]
    assert client.put("/api/v1/me/profile", headers=candidate_headers, json=candidate_profile).status_code == 200
    assert client.put(
        "/api/v1/me/match-preferences",
        headers=candidate_headers,
        json={"desiredDirections": ["AI"], "availabilitySlots": [], "version": 0},
    ).status_code == 200

    project_payload_value = project_payload()
    project_payload_value["roles"][0]["requiredSkills"] = ["Python"]
    project = client.post("/api/v1/projects", headers=owner_headers, json=project_payload_value).json()["data"]
    published = client.post(
        f"/api/v1/projects/{project['id']}/publish", headers=owner_headers, json={"version": project["version"]}
    ).json()["data"]
    role_id = published["roles"][0]["id"]

    owner_results = client.get(
        f"/api/v1/projects/{published['id']}/matches?roleId={role_id}&limit=1", headers=owner_headers
    )
    assert owner_results.status_code == 200
    assert owner_results.json()["data"][0]["targetType"] == "PROFILE"
    assert owner_results.json()["data"][0]["targetId"] == client.post(
        "/api/v1/auth/wechat/login", json={"code": "local:match-candidate", "consentAccepted": True}
    ).json()["data"]["userId"]
    assert owner_results.json()["meta"]["recommendationRequestId"].startswith("rrq_")
    recommendation_request_id = owner_results.json()["meta"]["recommendationRequestId"]
    impression = client.post(
        "/api/v1/recommendation-impressions",
        headers=owner_headers,
        json={
            "recommendationRequestId": recommendation_request_id,
            "items": [{"targetType": "PROFILE", "targetId": owner_results.json()["data"][0]["targetId"], "position": 1}],
            "occurredAt": datetime.now(UTC).isoformat(),
        },
    )
    assert impression.status_code == 200
    assert impression.json()["data"][0]["duplicate"] is False
    duplicate = client.post(
        "/api/v1/recommendation-impressions",
        headers=owner_headers,
        json={
            "recommendationRequestId": recommendation_request_id,
            "items": [{"targetType": "PROFILE", "targetId": owner_results.json()["data"][0]["targetId"], "position": 1}],
            "occurredAt": datetime.now(UTC).isoformat(),
        },
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["data"][0]["duplicate"] is True
    conflict = client.post(
        "/api/v1/recommendation-impressions",
        headers=owner_headers,
        json={
            "recommendationRequestId": recommendation_request_id,
            "items": [{"targetType": "PROFILE", "targetId": owner_results.json()["data"][0]["targetId"], "position": 2}],
            "occurredAt": datetime.now(UTC).isoformat(),
        },
    )
    assert conflict.status_code == 409
    assert client.post(
        "/api/v1/recommendation-impressions",
        headers=candidate_headers,
        json={
            "recommendationRequestId": recommendation_request_id,
            "items": [{"targetType": "PROFILE", "targetId": owner_results.json()["data"][0]["targetId"], "position": 1}],
            "occurredAt": datetime.now(UTC).isoformat(),
        },
    ).status_code == 422
    invalid_target = client.post(
        "/api/v1/recommendation-impressions",
        headers=owner_headers,
        json={
            "recommendationRequestId": recommendation_request_id,
            "items": [{"targetType": "PROFILE", "targetId": "usr_not_a_candidate", "position": 1}],
            "occurredAt": datetime.now(UTC).isoformat(),
        },
    )
    assert invalid_target.status_code == 422

    forbidden = client.get(
        f"/api/v1/projects/{published['id']}/matches?roleId={role_id}", headers=candidate_headers
    )
    assert forbidden.status_code == 403

    candidate_results = client.get("/api/v1/me/project-matches?limit=1", headers=candidate_headers)
    assert candidate_results.status_code == 200
    assert candidate_results.json()["data"][0]["targetType"] == "PROJECT_ROLE"
    assert candidate_results.json()["data"][0]["targetId"] == role_id

    invalid_cursor = client.get(
        f"/api/v1/projects/{published['id']}/matches?roleId={role_id}&cursor=rrq_invalid", headers=owner_headers
    )
    assert invalid_cursor.status_code == 422
    assert client.get("/api/v1/me/project-matches", headers=incomplete_headers).status_code == 409


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


def test_http_observability_log_is_structured_and_redacted(caplog) -> None:
    client = make_client()
    token = login(client, "observability")
    with caplog.at_level(logging.INFO, logger="teamup.http"):
        response = client.get(
            "/api/v1/me/profile?private_query=should_not_log",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    events = [record.message for record in caplog.records if record.name == "teamup.http"]
    assert events
    event = events[-1]
    assert '"event":"http_request_completed"' in event
    assert '"requestId":"' in event
    assert '"method":"GET"' in event
    assert '"path":"/api/v1/me/profile"' in event
    assert token not in event
    assert "private_query" not in event


def test_reports_validate_targets_and_are_idempotent() -> None:
    client = make_client()
    reporter_token = login(client, "reporter")
    target_token = login(client, "report-target")
    reporter_headers = {"Authorization": f"Bearer {reporter_token}"}
    target_headers = {"Authorization": f"Bearer {target_token}"}
    target_id = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "local:report-target", "consentAccepted": True},
    ).json()["data"]["userId"]
    payload = {
        "targetType": "USER",
        "targetId": target_id,
        "reason": "HARASSMENT",
        "description": "  重复骚扰  ",
    }
    created = client.post(
        "/api/v1/reports",
        headers={**reporter_headers, "X-Request-ID": "req_client_report_1"},
        json=payload,
    )
    assert created.status_code == 200
    assert created.headers["X-Request-ID"] == "req_client_report_1"
    assert created.json()["data"]["status"] == "PENDING"
    repeated = client.post("/api/v1/reports", headers=reporter_headers, json=payload)
    assert repeated.status_code == 200
    assert repeated.json()["data"]["id"] == created.json()["data"]["id"]
    assert client.post("/api/v1/reports", headers=target_headers, json=payload).status_code == 404
    assert client.post(
        "/api/v1/reports",
        headers=reporter_headers,
        json={**payload, "targetType": "MESSAGE", "targetId": "msg_private"},
    ).status_code == 404
    assert client.post("/api/v1/reports", json=payload).status_code == 401
    invalid_request_id = client.post(
        "/api/v1/reports",
        headers={**reporter_headers, "X-Request-ID": "unsafe request id"},
        json={**payload, "reason": "SPAM"},
    )
    assert invalid_request_id.status_code == 200
    assert invalid_request_id.headers["X-Request-ID"].startswith("req_")
    assert invalid_request_id.headers["X-Request-ID"] != "unsafe request id"


def test_account_deletion_request_revokes_all_sessions_and_blocks_login() -> None:
    client = make_client()
    first_token = login(client, "delete-account")
    second_token = login(client, "delete-account")
    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}
    response = client.post("/api/v1/account/deletion-requests", headers=first_headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "PENDING"
    assert client.get("/api/v1/me/profile", headers=first_headers).status_code == 401
    assert client.get("/api/v1/me/profile", headers=second_headers).status_code == 401
    relogin = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "local:delete-account", "consentAccepted": True},
    )
    assert relogin.status_code == 403


def test_account_deletion_removes_user_from_discovery_and_matching() -> None:
    client = make_client()
    owner_token = login(client, "deletion-filter-owner")
    candidate_token = login(client, "deletion-filter-candidate")
    viewer_token = login(client, "deletion-filter-viewer")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    candidate_id = client.post(
        "/api/v1/auth/wechat/login",
        json={"code": "local:deletion-filter-candidate", "consentAccepted": True},
    ).json()["data"]["userId"]

    assert client.put(
        "/api/v1/me/profile", headers=candidate_headers, json=profile_payload()
    ).status_code == 200
    assert client.put(
        "/api/v1/me/match-preferences",
        headers=candidate_headers,
        json={"desiredDirections": ["AI"], "availabilitySlots": [], "version": 0},
    ).status_code == 200
    candidate_project = client.post(
        "/api/v1/projects", headers=candidate_headers, json=project_payload()
    ).json()["data"]
    assert client.post(
        f"/api/v1/projects/{candidate_project['id']}/publish",
        headers=candidate_headers,
        json={"version": candidate_project["version"]},
    ).status_code == 200
    owner_project = client.post(
        "/api/v1/projects", headers=owner_headers, json=project_payload()
    ).json()["data"]
    owner_project = client.post(
        f"/api/v1/projects/{owner_project['id']}/publish",
        headers=owner_headers,
        json={"version": owner_project["version"]},
    ).json()["data"]
    role_id = owner_project["roles"][0]["id"]

    assert candidate_id in {
        item["id"] for item in client.get("/api/v1/profiles", headers=viewer_headers).json()["data"]
    }
    assert candidate_project["id"] in {
        item["id"] for item in client.get("/api/v1/projects", headers=viewer_headers).json()["data"]
    }
    assert candidate_id in {
        item["targetId"]
        for item in client.get(
            f"/api/v1/projects/{owner_project['id']}/matches?roleId={role_id}",
            headers=owner_headers,
        ).json()["data"]
    }

    assert client.post(
        "/api/v1/account/deletion-requests", headers=candidate_headers
    ).status_code == 200
    assert client.get(
        f"/api/v1/profiles/{candidate_id}", headers=viewer_headers
    ).status_code == 404
    assert candidate_id not in {
        item["id"] for item in client.get("/api/v1/profiles", headers=viewer_headers).json()["data"]
    }
    assert candidate_project["id"] not in {
        item["id"] for item in client.get("/api/v1/projects", headers=viewer_headers).json()["data"]
    }
    assert client.get(
        f"/api/v1/projects/{candidate_project['id']}", headers=viewer_headers
    ).status_code == 404
    assert candidate_id not in {
        item["targetId"]
        for item in client.get(
            f"/api/v1/projects/{owner_project['id']}/matches?roleId={role_id}",
            headers=owner_headers,
        ).json()["data"]
    }


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
