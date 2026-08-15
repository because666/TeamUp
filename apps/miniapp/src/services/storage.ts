import type {
  ContactCard,
  ContactExchangeRequest,
  ProfileDraft,
  ProjectDraft,
  ProjectInvitation,
} from "@/domain/models";

const PROFILE_KEY = "teamup.fixture.profile.v1";
const PROJECT_KEY = "teamup.fixture.project.v1";
const SESSION_KEY = "teamup.fixture.session.v1";
const CONTACT_CARD_KEY = "teamup.fixture.contact-card.v1";
const CONTACT_REQUESTS_KEY = "teamup.fixture.contact-requests.v1";
const PROJECT_INVITATIONS_KEY = "teamup.fixture.project-invitations.v1";
const PROFILE_RECOVERY_KEY = "teamup.local.profile-recovery.v1";
const PROJECT_RECOVERY_KEY = "teamup.local.project-recovery.v1";
const API_SESSION_KEY = "teamup.api.session.v1";

function normalizeProject(project: ProjectDraft | null): ProjectDraft | null {
  if (!project) return null;
  return {
    ...project,
    roles: (project.roles || []).map((role, index) => ({
      ...role,
      id: typeof role.id === "string" && role.id ? role.id : `fixture_role_local_${index + 1}`,
    })),
  };
}

export interface ApiSession {
  accessToken: string;
  userId: string;
}

export const fixtureStorage = {
  isSignedIn(): boolean {
    return uni.getStorageSync(SESSION_KEY) === "signed_in";
  },
  markSignedIn(): void {
    uni.setStorageSync(SESSION_KEY, "signed_in");
  },
  clearSession(): void {
    uni.removeStorageSync(SESSION_KEY);
  },
  readProfile(): ProfileDraft | null {
    return (uni.getStorageSync(PROFILE_KEY) || null) as ProfileDraft | null;
  },
  writeProfile(profile: ProfileDraft): void {
    uni.setStorageSync(PROFILE_KEY, profile);
  },
  readProject(): ProjectDraft | null {
    return normalizeProject((uni.getStorageSync(PROJECT_KEY) || null) as ProjectDraft | null);
  },
  writeProject(project: ProjectDraft): void {
    uni.setStorageSync(PROJECT_KEY, project);
  },
  readContactCard(): ContactCard | null {
    return (uni.getStorageSync(CONTACT_CARD_KEY) || null) as ContactCard | null;
  },
  writeContactCard(card: ContactCard): void {
    uni.setStorageSync(CONTACT_CARD_KEY, card);
  },
  readContactRequests(): ContactExchangeRequest[] | null {
    return (uni.getStorageSync(CONTACT_REQUESTS_KEY) || null) as ContactExchangeRequest[] | null;
  },
  writeContactRequests(requests: ContactExchangeRequest[]): void {
    uni.setStorageSync(CONTACT_REQUESTS_KEY, requests);
  },
  readProjectInvitations(): ProjectInvitation[] | null {
    return (uni.getStorageSync(PROJECT_INVITATIONS_KEY) || null) as ProjectInvitation[] | null;
  },
  writeProjectInvitations(invitations: ProjectInvitation[]): void {
    uni.setStorageSync(PROJECT_INVITATIONS_KEY, invitations);
  },
};

export const recoveryStorage = {
  readProfile(): ProfileDraft | null {
    return (uni.getStorageSync(PROFILE_RECOVERY_KEY) || null) as ProfileDraft | null;
  },
  writeProfile(profile: ProfileDraft): void {
    uni.setStorageSync(PROFILE_RECOVERY_KEY, profile);
  },
  clearProfile(): void {
    uni.removeStorageSync(PROFILE_RECOVERY_KEY);
  },
  readProject(): ProjectDraft | null {
    return normalizeProject((uni.getStorageSync(PROJECT_RECOVERY_KEY) || null) as ProjectDraft | null);
  },
  writeProject(project: ProjectDraft): void {
    uni.setStorageSync(PROJECT_RECOVERY_KEY, project);
  },
  clearProject(): void {
    uni.removeStorageSync(PROJECT_RECOVERY_KEY);
  },
};

export const apiSessionStorage = {
  read(): ApiSession | null {
    const value = uni.getStorageSync(API_SESSION_KEY) as Partial<ApiSession> | null;
    if (!value || typeof value.accessToken !== "string" || typeof value.userId !== "string") return null;
    if (!value.accessToken || !value.userId) return null;
    return { accessToken: value.accessToken, userId: value.userId };
  },
  write(session: ApiSession): void {
    uni.setStorageSync(API_SESSION_KEY, session);
  },
  clear(): void {
    uni.removeStorageSync(API_SESSION_KEY);
  },
};
