import { cloneProfile, cloneProject, fixtureEnvelope } from "@/domain/fixtures";
import {
  emptyProfileDraft,
  emptyProjectDraft,
  type DemoSession,
  type FixtureEnvelope,
  type ProfileDraft,
  type ProjectDraft,
  type ServiceEnvelope,
} from "@/domain/models";
import { isValid, validateProfile, validateProject } from "@/domain/validation";
import { apiBaseUrl, AppServiceError, isFixtureMode } from "./runtime";
import { apiSessionStorage, fixtureStorage } from "./storage";

type ApiMethod = "GET" | "POST" | "PUT";

interface ApiResponse<T> {
  data: T;
  requestId: string;
  meta?: Record<string, unknown>;
}

interface ApiSessionData {
  accessToken: string;
  tokenType: "Bearer";
  expiresIn: number;
  userId: string;
  profileState: "INCOMPLETE" | "COMPLETE";
}

interface ApiRoleData {
  name: string;
  skills: string[];
  headcount: number;
  hoursPerWeek: number;
  description?: string;
  status: "OPEN" | "CLOSED";
}

interface ApiProjectData {
  id: string;
  title: string;
  description: string;
  direction: string;
  competition?: string;
  stage: string;
  teamInfo?: string;
  status: "DRAFT" | "PUBLISHED" | "CLOSED";
  version: number;
  publishedAt?: string | null;
  roles: ApiRoleData[];
}

const wait = (duration = 420): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, duration));

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" ? value as Record<string, unknown> : {};
}

function asString(value: unknown, fallback: string): string {
  return typeof value === "string" && value ? value : fallback;
}

function appErrorFromResponse(statusCode: number, body: unknown): AppServiceError {
  const record = asRecord(body);
  const error = asRecord(record.error);
  const requestId = asString(record.requestId, "remote_request");
  const code = asString(error.code, statusCode >= 500 ? "REQUEST_FAILED" : "API_ERROR");
  const message = statusCode >= 500
    ? "服务暂时不可用，请稍后重试。"
    : asString(error.message, "请求未完成，请检查提交内容。");
  return new AppServiceError(code, message, statusCode || 503, requestId);
}

function request<T>(path: string, method: ApiMethod, data?: unknown, authenticated = true): Promise<ApiResponse<T>> {
  const session = authenticated ? apiSessionStorage.read() : null;
  const header: Record<string, string> = { "Content-Type": "application/json" };
  if (session?.accessToken) header.Authorization = `Bearer ${session.accessToken}`;

  return new Promise((resolve, reject) => {
    let baseUrl: string;
    try {
      baseUrl = apiBaseUrl();
    } catch (error) {
      reject(error);
      return;
    }

    uni.request({
      url: `${baseUrl}${path}`,
      method,
      data: data as UniApp.RequestOptions["data"],
      header,
      timeout: 10000,
      success: (response) => {
        const body = asRecord(response.data);
        const requestId = asString(body.requestId, "remote_request");
        if (response.statusCode >= 200 && response.statusCode < 300 && "data" in body) {
          resolve({
            data: body.data as T,
            meta: body.meta as Record<string, unknown> | undefined,
            requestId,
          });
          return;
        }
        if (response.statusCode === 401) apiSessionStorage.clear();
        reject(appErrorFromResponse(response.statusCode, response.data));
      },
      fail: () => reject(new AppServiceError("NETWORK_ERROR", "暂时无法连接服务，请检查网络后重试。", 503)),
    });
  });
}

function getWechatCode(): Promise<string> {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: "weixin",
      success: (result) => {
        const code = (result as { code?: unknown }).code;
        if (typeof code === "string" && code) resolve(code);
        else reject(new AppServiceError("WECHAT_LOGIN_UNAVAILABLE", "未获取到微信登录凭证。", 503));
      },
      fail: () => reject(new AppServiceError("WECHAT_LOGIN_UNAVAILABLE", "当前环境无法调用微信登录。", 503)),
    });
  });
}

function mapProject(data: ApiProjectData): ProjectDraft {
  return {
    id: data.id,
    title: data.title,
    description: data.description,
    direction: data.direction,
    competition: data.competition || "",
    stage: data.stage,
    teamInfo: data.teamInfo || "",
    status: data.status,
    version: data.version,
    publishedAt: data.publishedAt || null,
    roles: (data.roles || []).map((role) => ({
      name: role.name,
      skills: [...(role.skills || [])],
      headcount: role.headcount,
      hoursPerWeek: role.hoursPerWeek,
      description: role.description || "",
      status: role.status,
    })),
  };
}

function serializeProject(project: ProjectDraft): Record<string, unknown> {
  return {
    title: project.title,
    description: project.description,
    direction: project.direction,
    competition: project.competition,
    stage: project.stage,
    teamInfo: project.teamInfo,
    roles: project.roles.map((role) => ({
      name: role.name,
      skills: role.skills,
      headcount: role.headcount,
      hoursPerWeek: role.hoursPerWeek,
      description: role.description,
      status: role.status,
    })),
  };
}

async function apiLogin(consentAccepted: boolean): Promise<ServiceEnvelope<DemoSession>> {
  if (!consentAccepted) throw new AppServiceError("CONSENT_REQUIRED", "请先阅读并同意服务条款与隐私政策。", 422);
  const code = await getWechatCode();
  const response = await request<ApiSessionData>("/auth/wechat/login", "POST", { code, consentAccepted }, false);
  apiSessionStorage.write({ accessToken: response.data.accessToken, userId: response.data.userId });
  return {
    data: {
      state: response.data.profileState === "COMPLETE"
        ? "AUTHENTICATED"
        : "AUTHENTICATED_PROFILE_INCOMPLETE",
      displayName: "新同学",
    },
    meta: response.meta,
    requestId: response.requestId,
  };
}

async function apiLogout(): Promise<ServiceEnvelope<{ loggedOut: boolean }>> {
  const response = await request<{ loggedOut: boolean }>("/auth/logout", "POST");
  apiSessionStorage.clear();
  return { data: response.data, meta: response.meta, requestId: response.requestId };
}

async function apiGetProfile(): Promise<ServiceEnvelope<ProfileDraft>> {
  const response = await request<Record<string, unknown> | null>("/me/profile", "GET");
  return {
    data: response.data ? response.data as unknown as ProfileDraft : emptyProfileDraft(),
    meta: response.meta,
    requestId: response.requestId,
  };
}

async function apiSaveProfile(profile: ProfileDraft): Promise<ServiceEnvelope<ProfileDraft>> {
  const response = await request<ProfileDraft>("/me/profile", "PUT", profile);
  return { data: response.data, meta: response.meta, requestId: response.requestId };
}

async function apiGetProject(): Promise<ServiceEnvelope<ProjectDraft>> {
  const list = await request<ApiProjectData[]>("/me/projects?limit=1", "GET");
  const first = list.data?.[0];
  return {
    data: first ? mapProject(first) : emptyProjectDraft(),
    meta: list.meta,
    requestId: list.requestId,
  };
}

async function apiSaveProject(project: ProjectDraft): Promise<ServiceEnvelope<ProjectDraft>> {
  const payload = serializeProject(project);
  const response = project.id
    ? await request<ApiProjectData>(`/projects/${encodeURIComponent(project.id)}`, "PUT", {
      ...payload,
      version: project.version,
    })
    : await request<ApiProjectData>("/projects", "POST", payload);
  return { data: mapProject(response.data), meta: response.meta, requestId: response.requestId };
}

async function apiPublishProject(project: ProjectDraft): Promise<ServiceEnvelope<ProjectDraft>> {
  if (!project.id) throw new AppServiceError("VALIDATION_ERROR", "请先保存项目草稿。", 422);
  const response = await request<ApiProjectData>(
    `/projects/${encodeURIComponent(project.id)}/publish`,
    "POST",
    { version: project.version },
  );
  return { data: mapProject(response.data), meta: response.meta, requestId: response.requestId };
}

export const repository = {
  async login(consentAccepted: boolean): Promise<ServiceEnvelope<DemoSession> | FixtureEnvelope<DemoSession>> {
    if (!isFixtureMode()) return apiLogin(consentAccepted);
    await wait(520);
    if (!consentAccepted) {
      throw new AppServiceError("CONSENT_REQUIRED", "请先阅读并同意服务条款与隐私政策。", 422);
    }
    fixtureStorage.markSignedIn();
    const profile = fixtureStorage.readProfile();
    return fixtureEnvelope(
      {
        state: profile && isValid(validateProfile(profile))
          ? "AUTHENTICATED"
          : "AUTHENTICATED_PROFILE_INCOMPLETE",
        displayName: profile?.nickname || "新同学",
      },
      ["GAP-AUTH-01", "GAP-AUTH-02"],
    );
  },

  async logout(): Promise<ServiceEnvelope<{ loggedOut: boolean }> | FixtureEnvelope<{ loggedOut: boolean }>> {
    if (!isFixtureMode()) return apiLogout();
    fixtureStorage.clearSession();
    return fixtureEnvelope({ loggedOut: true }, ["GAP-AUTH-02"]);
  },

  async getProfile(): Promise<ServiceEnvelope<ProfileDraft> | FixtureEnvelope<ProfileDraft>> {
    if (!isFixtureMode()) return apiGetProfile();
    await wait();
    const profile = fixtureStorage.readProfile() || emptyProfileDraft();
    return fixtureEnvelope(cloneProfile(profile), ["GAP-PROF-01", "GAP-PROF-02"]);
  },

  async saveProfile(profile: ProfileDraft): Promise<ServiceEnvelope<ProfileDraft> | FixtureEnvelope<ProfileDraft>> {
    if (!isFixtureMode()) return apiSaveProfile(profile);
    await wait(560);
    const errors = validateProfile(profile);
    if (!isValid(errors)) {
      throw new AppServiceError("VALIDATION_ERROR", "能力名片还有必填信息未完成。", 422);
    }
    const saved = cloneProfile({ ...profile, version: profile.version + 1 });
    fixtureStorage.writeProfile(saved);
    return fixtureEnvelope(cloneProfile(saved), ["GAP-PROF-01", "GAP-PROF-02"]);
  },

  async getProject(): Promise<ServiceEnvelope<ProjectDraft> | FixtureEnvelope<ProjectDraft>> {
    if (!isFixtureMode()) return apiGetProject();
    await wait();
    const project = fixtureStorage.readProject() || emptyProjectDraft();
    return fixtureEnvelope(cloneProject(project), ["GAP-PROJ-01", "GAP-PROJ-03", "GAP-PROJ-04"]);
  },

  async saveProject(project: ProjectDraft): Promise<ServiceEnvelope<ProjectDraft> | FixtureEnvelope<ProjectDraft>> {
    if (!isFixtureMode()) return apiSaveProject(project);
    await wait(620);
    const saved = cloneProject({
      ...project,
      id: project.id || "fixture_project_owned_01",
      status: project.status === "PUBLISHED" ? "PUBLISHED" : "DRAFT",
      version: project.version + 1,
    });
    fixtureStorage.writeProject(saved);
    return fixtureEnvelope(cloneProject(saved), ["GAP-PROJ-01", "GAP-PROJ-04"]);
  },

  async publishProject(project: ProjectDraft): Promise<ServiceEnvelope<ProjectDraft> | FixtureEnvelope<ProjectDraft>> {
    if (!isFixtureMode()) return apiPublishProject(project);
    await wait(760);
    if (!isValid(validateProject(project))) {
      throw new AppServiceError("VALIDATION_ERROR", "项目或开放岗位信息不完整。", 422);
    }
    const published = cloneProject({
      ...project,
      id: project.id || "fixture_project_owned_01",
      status: "PUBLISHED",
      version: project.version + 1,
      publishedAt: new Date().toISOString(),
    });
    fixtureStorage.writeProject(published);
    return fixtureEnvelope(cloneProject(published), ["GAP-PROJ-02", "GAP-PROJ-04"]);
  },
};
