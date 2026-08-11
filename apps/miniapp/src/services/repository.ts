import { cloneProfile, cloneProject, fixtureEnvelope } from "@/domain/fixtures";
import {
  emptyProfileDraft,
  emptyProjectDraft,
  type DemoSession,
  type FixtureEnvelope,
  type ProfileDraft,
  type ProjectDraft,
} from "@/domain/models";
import { isValid, validateProfile, validateProject } from "@/domain/validation";
import { AppServiceError, requireFixtureMode } from "./runtime";
import { fixtureStorage } from "./storage";

const wait = (duration = 420): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, duration));

export const repository = {
  async login(consentAccepted: boolean): Promise<FixtureEnvelope<DemoSession>> {
    requireFixtureMode();
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

  async getProfile(): Promise<FixtureEnvelope<ProfileDraft>> {
    requireFixtureMode();
    await wait();
    const profile = fixtureStorage.readProfile() || emptyProfileDraft();
    return fixtureEnvelope(cloneProfile(profile), ["GAP-PROF-01", "GAP-PROF-02"]);
  },

  async saveProfile(profile: ProfileDraft): Promise<FixtureEnvelope<ProfileDraft>> {
    requireFixtureMode();
    await wait(560);
    const errors = validateProfile(profile);
    if (!isValid(errors)) {
      throw new AppServiceError("VALIDATION_ERROR", "能力名片还有必填信息未完成。", 422);
    }
    const saved = cloneProfile({ ...profile, version: profile.version + 1 });
    fixtureStorage.writeProfile(saved);
    return fixtureEnvelope(cloneProfile(saved), ["GAP-PROF-01", "GAP-PROF-02"]);
  },

  async getProject(): Promise<FixtureEnvelope<ProjectDraft>> {
    requireFixtureMode();
    await wait();
    const project = fixtureStorage.readProject() || emptyProjectDraft();
    return fixtureEnvelope(cloneProject(project), [
      "GAP-PROJ-01",
      "GAP-PROJ-03",
      "GAP-PROJ-04",
    ]);
  },

  async saveProject(project: ProjectDraft): Promise<FixtureEnvelope<ProjectDraft>> {
    requireFixtureMode();
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

  async publishProject(project: ProjectDraft): Promise<FixtureEnvelope<ProjectDraft>> {
    requireFixtureMode();
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
