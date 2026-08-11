from fastapi.testclient import TestClient

from app.config import Settings
from app.main import make_app


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
