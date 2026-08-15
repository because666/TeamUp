import { afterEach, describe, expect, it, vi } from "vitest";
import { emptyProjectDraft } from "@/domain/models";

interface RequestOptions {
  url: string;
  method: string;
  data?: unknown;
  header?: Record<string, string>;
  success: (response: { statusCode: number; data: unknown }) => void;
  fail: () => void;
}

function installUniMock(
  handler: (options: RequestOptions) => void,
  storage = new Map<string, unknown>(),
): { request: ReturnType<typeof vi.fn>; storage: Map<string, unknown> } {
  const request = vi.fn((options: RequestOptions) => handler(options));
  vi.stubGlobal("uni", {
    login: ({ success }: { success: (result: { code: string }) => void }) => success({ code: "wx_code_01" }),
    request,
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
    removeStorageSync: (key: string) => storage.delete(key),
  });
  return { request, storage };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("API repository", () => {
  it("exchanges a real WeChat code and stores only the platform session", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const mock = installUniMock((options) => {
      options.success({
        statusCode: 200,
        data: {
          data: {
            accessToken: "access_01",
            tokenType: "Bearer",
            expiresIn: 3600,
            userId: "usr_01",
            profileState: "INCOMPLETE",
          },
          requestId: "req_login_01",
        },
      });
    });
    const { repository } = await import("./repository");

    const response = await repository.login(true);

    expect(response.data.state).toBe("AUTHENTICATED_PROFILE_INCOMPLETE");
    expect(response.requestId).toBe("req_login_01");
    expect(mock.request).toHaveBeenCalledOnce();
    const request = mock.request.mock.calls[0][0] as RequestOptions;
    expect(request.url).toBe("https://api.teamup.test/api/v1/auth/wechat/login");
    expect(request.method).toBe("POST");
    expect(request.data).toEqual({ code: "wx_code_01", consentAccepted: true });
    expect(mock.storage.get("teamup.api.session.v1")).toEqual({
      accessToken: "access_01",
      userId: "usr_01",
    });
  });

  it("preserves server error code and request id without exposing transport details", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    installUniMock((options) => {
      options.success({
        statusCode: 409,
        data: {
          error: { code: "VERSION_CONFLICT", message: "请重新加载最新版本。" },
          requestId: "req_conflict_01",
        },
      });
    });
    const { repository } = await import("./repository");

    await expect(repository.saveProfile({
      nickname: "Lin",
      school: "TeamUp University",
      major: "Software Engineering",
      grade: "大三",
      skills: ["Python"],
      collaborationScenarios: ["竞赛"],
      rolePreference: "MEMBER",
      hoursPerWeek: 8,
      bio: "",
      visibility: false,
      version: 1,
    })).rejects.toMatchObject({
      code: "VERSION_CONFLICT",
      status: 409,
      requestId: "req_conflict_01",
    });
  });

  it("sends the bearer token on logout and clears the local API session after success", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const storage = new Map<string, unknown>([[
      "teamup.api.session.v1",
      { accessToken: "access_01", userId: "usr_01" },
    ]]);
    let authorization = "";
    installUniMock((options) => {
      authorization = options.header?.Authorization || "";
      options.success({
        statusCode: 200,
        data: { data: { loggedOut: true }, requestId: "req_logout_01" },
      });
    }, storage);
    const { repository } = await import("./repository");

    const response = await repository.logout();

    expect(response.data.loggedOut).toBe(true);
    expect(authorization).toBe("Bearer access_01");
    expect(storage.has("teamup.api.session.v1")).toBe(false);
  });

  it("clears a rejected session when the backend returns 401", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const storage = new Map<string, unknown>([[
      "teamup.api.session.v1",
      { accessToken: "expired_access", userId: "usr_01" },
    ]]);
    installUniMock((options) => {
      options.success({
        statusCode: 401,
        data: { error: { code: "AUTH_REQUIRED", message: "请重新登录。" }, requestId: "req_401" },
      });
    }, storage);
    const { repository } = await import("./repository");

    await expect(repository.getProfile()).rejects.toMatchObject({ status: 401, requestId: "req_401" });
    expect(storage.has("teamup.api.session.v1")).toBe(false);
  });

  it("preserves authentication handling through the CloudBase transport", async () => {
    vi.stubEnv("MODE", "cloudbase");
    vi.stubEnv("VITE_CLOUDBASE_ENV_ID", "teamup-dev-01");
    vi.stubEnv("VITE_CLOUDBASE_SERVICE", "teamup-api");
    const storage = new Map<string, unknown>([[
      "teamup.api.session.v1",
      { accessToken: "expired_access", userId: "usr_01" },
    ]]);
    installUniMock(() => undefined, storage);
    const callContainer = vi.fn().mockResolvedValue({
      statusCode: 401,
      data: { error: { code: "AUTH_REQUIRED", message: "请重新登录。" }, requestId: "req_cloud_401" },
    });
    vi.stubGlobal("wx", { cloud: { init: vi.fn(), callContainer } });
    const { repository } = await import("./repository");

    await expect(repository.getProfile()).rejects.toMatchObject({
      status: 401,
      requestId: "req_cloud_401",
    });
    expect(storage.has("teamup.api.session.v1")).toBe(false);
    expect(callContainer).toHaveBeenCalledWith(expect.objectContaining({
      path: "/api/v1/me/profile",
      method: "GET",
      header: expect.objectContaining({
        Authorization: "Bearer expired_access",
        "X-WX-SERVICE": "teamup-api",
      }),
    }));
  });

  it("uses POST for a new project and WeChat-compatible PUT with version for an existing project", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const methods: Array<{ method: string; data: unknown }> = [];
    installUniMock((options) => {
      methods.push({ method: options.method, data: options.data });
      options.success({
        statusCode: 200,
        data: {
          data: {
            id: "prj_01",
            title: "TeamUp",
            description: "Build a team platform",
            direction: "AI",
            competition: "Innovation Contest",
            stage: "DEVELOPMENT",
            teamInfo: "Two members",
            status: "DRAFT",
            version: methods.length,
            publishedAt: null,
            roles: [{
              id: "role_backend_01",
              name: "Backend",
              skills: ["Python"],
              headcount: 1,
              hoursPerWeek: 8,
              description: "API",
              status: "OPEN",
            }],
          },
          requestId: `req_project_${methods.length}`,
        },
      });
    });
    const { repository } = await import("./repository");
    const draft = {
      ...emptyProjectDraft(),
      title: "TeamUp",
      description: "Build a team platform",
      direction: "AI",
      competition: "Innovation Contest",
      stage: "DEVELOPMENT",
      teamInfo: "Two members",
      roles: [{
        id: "",
        name: "Backend",
        skills: ["Python"],
        headcount: 1,
        hoursPerWeek: 8,
        description: "API",
        status: "OPEN" as const,
      }],
    };

    const created = await repository.saveProject(draft);
    await repository.saveProject(created.data);

    expect(methods[0].method).toBe("POST");
    expect(methods[1].method).toBe("PUT");
    expect(methods[1].data).toMatchObject({ version: 1 });
  });

  it("loads a selected public project through the confirmed project detail endpoint", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const mock = installUniMock((options) => {
      options.success({
        statusCode: 200,
        data: {
          data: {
            id: "project_public_01",
            ownerId: "user_owner_01",
            title: "Campus Project",
            description: "Public detail",
            direction: "Green Tech",
            competition: "Innovation Contest",
            stage: "PROTOTYPE",
            teamInfo: "Two members",
            status: "PUBLISHED",
            version: 2,
            publishedAt: "2026-08-10T08:00:00Z",
            roles: [{
              id: "role_data_01",
              name: "Data Analyst",
              skills: ["Python"],
              headcount: 1,
              hoursPerWeek: 6,
              description: "Analyze routes",
              status: "OPEN",
            }],
          },
          requestId: "req_project_detail_01",
        },
      });
    });
    const { repository } = await import("./repository");

    const response = await repository.getProjectById("project_public_01");

    expect(response.data.title).toBe("Campus Project");
    expect(response.data.ownerId).toBe("user_owner_01");
    const request = mock.request.mock.calls[0][0] as RequestOptions;
    expect(request.url).toBe("https://api.teamup.test/api/v1/projects/project_public_01");
    expect(request.method).toBe("GET");
  });

  it("creates a contact exchange request from project and role ids only", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const mock = installUniMock((options) => {
      options.success({
        statusCode: 200,
        data: {
          data: {
            id: "contact_request_01",
            projectId: "project_public_01",
            roleId: "role_data_01",
            projectTitle: "Campus Project",
            roleName: "Data Analyst",
            requesterUserId: "user_current_01",
            recipientUserId: "user_owner_01",
            box: "SENT",
            peerDisplayName: "Organizer",
            status: "PENDING",
            peerContactCard: null,
            createdAt: "2026-08-15T00:00:00Z",
            respondedAt: null,
          },
          requestId: "req_contact_01",
        },
      });
    });
    const { repository } = await import("./repository");

    const response = await repository.createContactExchangeRequest("project_public_01", "role_data_01");

    expect(response.data.id).toBe("contact_request_01");
    const request = mock.request.mock.calls[0][0] as RequestOptions;
    expect(request.url).toBe("https://api.teamup.test/api/v1/contact-exchange-requests");
    expect(request.method).toBe("POST");
    expect(request.data).toEqual({
      projectId: "project_public_01",
      roleId: "role_data_01",
    });
  });

  it("rejects a contact request without an opaque role id", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const mock = installUniMock(() => undefined);
    const { repository } = await import("./repository");

    await expect(repository.createContactExchangeRequest("project_public_01", "")).rejects.toMatchObject({
      code: "VALIDATION_ERROR",
      status: 422,
    });
    expect(mock.request).not.toHaveBeenCalled();
  });

  it("updates a contact request without sending any contact value in the action body", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const mock = installUniMock((options) => {
      options.success({
        statusCode: 200,
        data: {
          data: {
            id: "contact_request_01",
            projectId: "project_public_01",
            roleId: "role_data_01",
            projectTitle: "Campus Project",
            roleName: "Data Analyst",
            requesterUserId: "user_requester_01",
            recipientUserId: "user_current_01",
            box: "RECEIVED",
            peerDisplayName: "Candidate",
            status: "ACCEPTED",
            peerContactCard: {
              methods: [{ type: "WECHAT", value: "candidate_01" }],
              version: 1,
              updatedAt: "2026-08-15T00:00:00Z",
            },
            createdAt: "2026-08-15T00:00:00Z",
            respondedAt: "2026-08-15T01:00:00Z",
          },
          requestId: "req_contact_accept_01",
        },
      });
    });
    const { repository } = await import("./repository");

    const response = await repository.actOnContactExchangeRequest("contact_request_01", "accept");

    expect(response.data.peerContactCard?.methods[0].value).toBe("candidate_01");
    const request = mock.request.mock.calls[0][0] as RequestOptions;
    expect(request.url).toBe(
      "https://api.teamup.test/api/v1/contact-exchange-requests/contact_request_01/accept",
    );
    expect(request.method).toBe("POST");
    expect(request.data).toBeUndefined();
  });

  it("saves only editable contact-card fields", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const mock = installUniMock((options) => {
      options.success({
        statusCode: 200,
        data: {
          data: {
            methods: [{ type: "WECHAT", value: "teamup_user" }],
            version: 3,
            updatedAt: "2026-08-15T02:00:00Z",
          },
          requestId: "req_contact_card_01",
        },
      });
    });
    const { repository } = await import("./repository");

    await repository.saveContactCard({
      methods: [{ type: "WECHAT", value: "teamup_user" }],
      version: 2,
      updatedAt: "2026-08-15T01:00:00Z",
    });

    const request = mock.request.mock.calls[0][0] as RequestOptions;
    expect(request.url).toBe("https://api.teamup.test/api/v1/me/contact-card");
    expect(request.method).toBe("PUT");
    expect(request.data).toEqual({
      methods: [{ type: "WECHAT", value: "teamup_user" }],
      version: 2,
    });
  });

  it("lists received project invitations and normalizes an accept response", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.teamup.test/api/v1");
    const mock = installUniMock((options) => {
      if (options.url.endsWith("/me/invitations?box=RECEIVED")) {
        options.success({
          statusCode: 200,
          data: {
            data: [{
              id: "invitation_01",
              projectId: "project_01",
              roleId: "role_01",
              projectTitle: "Campus Project",
              roleName: "Frontend",
              inviterUserId: "owner_01",
              inviteeUserId: "user_01",
              box: "RECEIVED",
              peerDisplayName: "Organizer",
              status: "PENDING",
              expiresAt: "2026-08-22T00:00:00Z",
              createdAt: "2026-08-15T00:00:00Z",
              respondedAt: null,
            }],
            requestId: "req_invitation_list_01",
          },
        });
        return;
      }
      options.success({
        statusCode: 200,
        data: {
          data: {
            invitation: {
              id: "invitation_01",
              projectId: "project_01",
              roleId: "role_01",
              inviterUserId: "owner_01",
              inviteeUserId: "user_01",
              status: "ACCEPTED",
              expiresAt: "2026-08-22T00:00:00Z",
              createdAt: "2026-08-15T00:00:00Z",
              respondedAt: "2026-08-15T03:00:00Z",
            },
            member: { id: "member_01" },
          },
          requestId: "req_invitation_accept_01",
        },
      });
    });
    const { repository } = await import("./repository");

    const listed = await repository.listProjectInvitations("RECEIVED");
    const accepted = await repository.actOnProjectInvitation("invitation_01", "accept");

    expect(listed.data[0].projectTitle).toBe("Campus Project");
    expect(accepted.data.status).toBe("ACCEPTED");
    const listRequest = mock.request.mock.calls[0][0] as RequestOptions;
    const acceptRequest = mock.request.mock.calls[1][0] as RequestOptions;
    expect(listRequest.url).toBe("https://api.teamup.test/api/v1/me/invitations?box=RECEIVED");
    expect(listRequest.method).toBe("GET");
    expect(acceptRequest.url).toBe(
      "https://api.teamup.test/api/v1/invitations/invitation_01/accept",
    );
    expect(acceptRequest.method).toBe("POST");
    expect(acceptRequest.data).toBeUndefined();
  });
});
