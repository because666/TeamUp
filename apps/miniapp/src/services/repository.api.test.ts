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
});
