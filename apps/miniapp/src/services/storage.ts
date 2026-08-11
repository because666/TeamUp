import type { ProfileDraft, ProjectDraft } from "@/domain/models";

const PROFILE_KEY = "teamup.fixture.profile.v1";
const PROJECT_KEY = "teamup.fixture.project.v1";
const SESSION_KEY = "teamup.fixture.session.v1";
const PROFILE_RECOVERY_KEY = "teamup.local.profile-recovery.v1";
const PROJECT_RECOVERY_KEY = "teamup.local.project-recovery.v1";

export const fixtureStorage = {
  isSignedIn(): boolean {
    return uni.getStorageSync(SESSION_KEY) === "signed_in";
  },
  markSignedIn(): void {
    uni.setStorageSync(SESSION_KEY, "signed_in");
  },
  readProfile(): ProfileDraft | null {
    return (uni.getStorageSync(PROFILE_KEY) || null) as ProfileDraft | null;
  },
  writeProfile(profile: ProfileDraft): void {
    uni.setStorageSync(PROFILE_KEY, profile);
  },
  readProject(): ProjectDraft | null {
    return (uni.getStorageSync(PROJECT_KEY) || null) as ProjectDraft | null;
  },
  writeProject(project: ProjectDraft): void {
    uni.setStorageSync(PROJECT_KEY, project);
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
    return (uni.getStorageSync(PROJECT_RECOVERY_KEY) || null) as ProjectDraft | null;
  },
  writeProject(project: ProjectDraft): void {
    uni.setStorageSync(PROJECT_RECOVERY_KEY, project);
  },
  clearProject(): void {
    uni.removeStorageSync(PROJECT_RECOVERY_KEY);
  },
};
