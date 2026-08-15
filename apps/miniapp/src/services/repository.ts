import {
  cloneContactRequests,
  cloneProfile,
  cloneProject,
  cloneProjectInvitations,
  discoveryProjectDetails,
  fixtureEnvelope,
  initialFixtureContactRequests,
  initialFixtureProjectInvitations,
} from "@/domain/fixtures";
import {
  emptyProfileDraft,
  emptyProjectDraft,
  type ContactCard,
  type ContactExchangeBox,
  type ContactExchangeRequest,
  type DemoSession,
  type FixtureEnvelope,
  type ProfileDraft,
  type ProjectDraft,
  type ProjectInvitation,
  type ProjectInvitationBox,
  type ProjectInvitationRecord,
  type ServiceEnvelope,
} from "@/domain/models";
import {
  isValid,
  validateContactCard,
  validateProfile,
  validateProject,
} from "@/domain/validation";
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
  id: string;
  name: string;
  skills: string[];
  headcount: number;
  hoursPerWeek: number;
  description?: string;
  status: "OPEN" | "CLOSED";
}

interface ApiProjectData {
  id: string;
  ownerId: string;
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
    ownerId: data.ownerId,
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
      id: role.id,
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

async function apiGetProjectById(projectId: string): Promise<ServiceEnvelope<ProjectDraft>> {
  const response = await request<ApiProjectData>(`/projects/${encodeURIComponent(projectId)}`, "GET");
  return { data: mapProject(response.data), meta: response.meta, requestId: response.requestId };
}

async function apiGetContactCard(): Promise<ServiceEnvelope<ContactCard | null>> {
  const response = await request<ContactCard | null>("/me/contact-card", "GET");
  return { data: response.data, meta: response.meta, requestId: response.requestId };
}

async function apiSaveContactCard(card: ContactCard): Promise<ServiceEnvelope<ContactCard>> {
  const response = await request<ContactCard>("/me/contact-card", "PUT", {
    methods: card.methods,
    version: card.version,
  });
  return { data: response.data, meta: response.meta, requestId: response.requestId };
}

async function apiCreateContactExchangeRequest(
  projectId: string,
  roleId: string,
): Promise<ServiceEnvelope<ContactExchangeRequest>> {
  const response = await request<ContactExchangeRequest>("/contact-exchange-requests", "POST", {
    projectId,
    roleId,
  });
  return { data: response.data, meta: response.meta, requestId: response.requestId };
}

async function apiListContactExchangeRequests(
  box: ContactExchangeBox,
): Promise<ServiceEnvelope<ContactExchangeRequest[]>> {
  const response = await request<ContactExchangeRequest[]>(
    `/me/contact-exchange-requests?box=${box}`,
    "GET",
  );
  return { data: response.data, meta: response.meta, requestId: response.requestId };
}

async function apiActOnContactExchangeRequest(
  requestId: string,
  action: "accept" | "reject" | "cancel",
): Promise<ServiceEnvelope<ContactExchangeRequest>> {
  const response = await request<ContactExchangeRequest>(
    `/contact-exchange-requests/${encodeURIComponent(requestId)}/${action}`,
    "POST",
  );
  return { data: response.data, meta: response.meta, requestId: response.requestId };
}

async function apiListProjectInvitations(
  box: ProjectInvitationBox,
): Promise<ServiceEnvelope<ProjectInvitation[]>> {
  const response = await request<ProjectInvitation[]>(`/me/invitations?box=${box}`, "GET");
  return { data: response.data, meta: response.meta, requestId: response.requestId };
}

async function apiActOnProjectInvitation(
  invitationId: string,
  action: "accept" | "reject",
): Promise<ServiceEnvelope<ProjectInvitationRecord>> {
  if (action === "accept") {
    const response = await request<{ invitation: ProjectInvitationRecord }>(
      `/invitations/${encodeURIComponent(invitationId)}/accept`,
      "POST",
    );
    return {
      data: response.data.invitation,
      meta: response.meta,
      requestId: response.requestId,
    };
  }
  const response = await request<ProjectInvitationRecord>(
    `/invitations/${encodeURIComponent(invitationId)}/reject`,
    "POST",
  );
  return { data: response.data, meta: response.meta, requestId: response.requestId };
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

  async getProjectById(projectId: string): Promise<ServiceEnvelope<ProjectDraft> | FixtureEnvelope<ProjectDraft>> {
    if (!isFixtureMode()) return apiGetProjectById(projectId);
    await wait();
    const project = discoveryProjectDetails.find((item) => item.id === projectId);
    if (!project) {
      throw new AppServiceError("RESOURCE_NOT_FOUND", "项目不存在或暂不可见。", 404);
    }
    return fixtureEnvelope(cloneProject(project), ["GAP-PROJ-04"]);
  },

  async getContactCard(): Promise<ServiceEnvelope<ContactCard | null> | FixtureEnvelope<ContactCard | null>> {
    if (!isFixtureMode()) return apiGetContactCard();
    await wait(300);
    const card = fixtureStorage.readContactCard();
    return fixtureEnvelope(card ? JSON.parse(JSON.stringify(card)) as ContactCard : null, ["GAP-CONTACT-01"]);
  },

  async saveContactCard(card: ContactCard): Promise<ServiceEnvelope<ContactCard> | FixtureEnvelope<ContactCard>> {
    if (!isValid(validateContactCard(card))) {
      throw new AppServiceError("VALIDATION_ERROR", "请检查填写的联系方式。", 422);
    }
    if (!isFixtureMode()) return apiSaveContactCard(card);
    await wait(420);
    const current = fixtureStorage.readContactCard();
    if (current && current.version !== card.version) {
      throw new AppServiceError("VERSION_CONFLICT", "联系名片已被更新，请重新加载。", 409);
    }
    if (!current && card.version !== 0) {
      throw new AppServiceError("VERSION_CONFLICT", "联系名片已被更新，请重新加载。", 409);
    }
    const saved: ContactCard = {
      methods: card.methods.map((method) => ({ ...method, value: method.value.trim() })),
      version: current ? current.version + 1 : 1,
      updatedAt: new Date().toISOString(),
    };
    fixtureStorage.writeContactCard(saved);
    return fixtureEnvelope(JSON.parse(JSON.stringify(saved)) as ContactCard, ["GAP-CONTACT-01"]);
  },

  async createContactExchangeRequest(
    projectId: string,
    roleId: string,
  ): Promise<ServiceEnvelope<ContactExchangeRequest> | FixtureEnvelope<ContactExchangeRequest>> {
    if (!projectId || !roleId) {
      throw new AppServiceError("VALIDATION_ERROR", "项目或岗位信息不完整。", 422);
    }
    if (!isFixtureMode()) return apiCreateContactExchangeRequest(projectId, roleId);
    await wait(420);
    if (!fixtureStorage.readContactCard()) {
      throw new AppServiceError("CONTACT_CARD_REQUIRED", "请先填写自己的联系方式。", 409);
    }
    const project = discoveryProjectDetails.find((item) => item.id === projectId);
    const role = project?.roles.find((item) => item.id === roleId);
    if (!project || project.status !== "PUBLISHED" || !role || role.status !== "OPEN") {
      throw new AppServiceError("RESOURCE_NOT_FOUND", "项目或岗位不存在或不可联系。", 404);
    }
    const requests = fixtureStorage.readContactRequests()
      || cloneContactRequests(initialFixtureContactRequests);
    const existing = requests.find((item) => (
      item.box === "SENT"
      && item.projectId === projectId
      && item.roleId === roleId
      && (item.status === "PENDING" || item.status === "ACCEPTED")
    ));
    if (existing) return fixtureEnvelope({ ...existing }, ["GAP-CONTACT-01"]);
    const created: ContactExchangeRequest = {
      id: `fixture_contact_request_${Date.now()}`,
      projectId,
      roleId,
      projectTitle: project.title,
      roleName: role.name,
      requesterUserId: "fixture_user_current_01",
      recipientUserId: project.ownerId || "fixture_user_owner",
      box: "SENT",
      peerDisplayName: "项目联系人",
      status: "PENDING",
      peerContactCard: null,
      createdAt: new Date().toISOString(),
      respondedAt: null,
    };
    requests.unshift(created);
    fixtureStorage.writeContactRequests(requests);
    return fixtureEnvelope({ ...created }, ["GAP-CONTACT-01"]);
  },

  async listContactExchangeRequests(
    box: ContactExchangeBox,
  ): Promise<ServiceEnvelope<ContactExchangeRequest[]> | FixtureEnvelope<ContactExchangeRequest[]>> {
    if (!isFixtureMode()) return apiListContactExchangeRequests(box);
    await wait(360);
    const requests = fixtureStorage.readContactRequests()
      || cloneContactRequests(initialFixtureContactRequests);
    fixtureStorage.writeContactRequests(requests);
    return fixtureEnvelope(
      cloneContactRequests(requests.filter((item) => item.box === box)),
      ["GAP-CONTACT-01"],
    );
  },

  async actOnContactExchangeRequest(
    requestId: string,
    action: "accept" | "reject" | "cancel",
  ): Promise<ServiceEnvelope<ContactExchangeRequest> | FixtureEnvelope<ContactExchangeRequest>> {
    if (!requestId) throw new AppServiceError("VALIDATION_ERROR", "联系申请信息不完整。", 422);
    if (!isFixtureMode()) return apiActOnContactExchangeRequest(requestId, action);
    await wait(360);
    const requests = fixtureStorage.readContactRequests()
      || cloneContactRequests(initialFixtureContactRequests);
    const index = requests.findIndex((item) => item.id === requestId);
    if (index < 0) throw new AppServiceError("RESOURCE_NOT_FOUND", "联系申请不存在或不可见。", 404);
    const current = requests[index];
    const expectedBox = action === "cancel" ? "SENT" : "RECEIVED";
    if (current.box !== expectedBox) {
      throw new AppServiceError("RESOURCE_NOT_FOUND", "联系申请不存在或不可见。", 404);
    }
    const terminal = action === "accept" ? "ACCEPTED" : action === "reject" ? "REJECTED" : "CANCELLED";
    if (current.status === terminal) return fixtureEnvelope({ ...current }, ["GAP-CONTACT-01"]);
    if (current.status !== "PENDING") {
      throw new AppServiceError("CONTACT_REQUEST_NOT_ACTIONABLE", "联系申请已处理。", 409);
    }
    if (action === "accept" && !fixtureStorage.readContactCard()) {
      throw new AppServiceError("CONTACT_CARD_REQUIRED", "请先填写自己的联系方式。", 409);
    }
    const updated: ContactExchangeRequest = {
      ...current,
      status: terminal,
      respondedAt: new Date().toISOString(),
      peerContactCard: action === "accept"
        ? {
          methods: [{ type: "WECHAT", value: "fixture_candidate_01" }],
          version: 1,
          updatedAt: new Date().toISOString(),
        }
        : null,
    };
    requests[index] = updated;
    fixtureStorage.writeContactRequests(requests);
    return fixtureEnvelope({ ...updated }, ["GAP-CONTACT-01"]);
  },

  async listProjectInvitations(
    box: ProjectInvitationBox,
  ): Promise<ServiceEnvelope<ProjectInvitation[]> | FixtureEnvelope<ProjectInvitation[]>> {
    if (!isFixtureMode()) return apiListProjectInvitations(box);
    await wait(360);
    const invitations = fixtureStorage.readProjectInvitations()
      || cloneProjectInvitations(initialFixtureProjectInvitations);
    fixtureStorage.writeProjectInvitations(invitations);
    return fixtureEnvelope(
      cloneProjectInvitations(invitations.filter((item) => item.box === box)),
      ["GAP-CONTACT-01"],
    );
  },

  async actOnProjectInvitation(
    invitationId: string,
    action: "accept" | "reject",
  ): Promise<ServiceEnvelope<ProjectInvitationRecord> | FixtureEnvelope<ProjectInvitationRecord>> {
    if (!invitationId) throw new AppServiceError("VALIDATION_ERROR", "邀请信息不完整。", 422);
    if (!isFixtureMode()) return apiActOnProjectInvitation(invitationId, action);
    await wait(360);
    const invitations = fixtureStorage.readProjectInvitations()
      || cloneProjectInvitations(initialFixtureProjectInvitations);
    const index = invitations.findIndex((item) => item.id === invitationId);
    if (index < 0 || invitations[index].box !== "RECEIVED") {
      throw new AppServiceError("RESOURCE_NOT_FOUND", "邀请不存在或不可见。", 404);
    }
    const current = invitations[index];
    const terminal = action === "accept" ? "ACCEPTED" : "REJECTED";
    if (current.status === terminal) return fixtureEnvelope({ ...current }, ["GAP-CONTACT-01"]);
    if (current.status !== "PENDING") {
      throw new AppServiceError("INVITATION_NOT_ACTIONABLE", "邀请已处理或已过期。", 409);
    }
    const updated: ProjectInvitation = {
      ...current,
      status: terminal,
      respondedAt: new Date().toISOString(),
    };
    invitations[index] = updated;
    fixtureStorage.writeProjectInvitations(invitations);
    return fixtureEnvelope({ ...updated }, ["GAP-CONTACT-01"]);
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
