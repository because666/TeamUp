export type ContractStatus = "PROPOSED_GAP";

export interface ServiceEnvelope<T> {
  requestId: string;
  data: T;
  meta?: Record<string, unknown>;
}

export interface FixtureEnvelope<T> extends ServiceEnvelope<T> {
  _fixture: true;
  contractStatus: ContractStatus;
  gapIds: string[];
}

export type UserState =
  | "GUEST"
  | "AUTHENTICATED_PROFILE_INCOMPLETE"
  | "AUTHENTICATED";

export interface DemoSession {
  state: UserState;
  displayName: string;
}

export interface ProfileDraft {
  nickname: string;
  school: string;
  major: string;
  grade: string;
  skills: string[];
  collaborationScenarios: string[];
  rolePreference: "LEADER" | "MEMBER" | "FLEXIBLE" | "";
  hoursPerWeek: number;
  bio: string;
  visibility: boolean;
  version: number;
}

export interface RecruitmentRoleDraft {
  name: string;
  skills: string[];
  headcount: number;
  hoursPerWeek: number;
  description: string;
  status: "OPEN" | "CLOSED";
}

export interface ProjectDraft {
  id: string;
  title: string;
  description: string;
  direction: string;
  competition: string;
  stage: string;
  teamInfo: string;
  status: "DRAFT" | "PUBLISHED" | "CLOSED";
  version: number;
  publishedAt: string | null;
  roles: RecruitmentRoleDraft[];
}

export interface DiscoveryProject {
  id: string;
  title: string;
  direction: string;
  stage: string;
  summary: string;
  skills: string[];
  openRoleCount: number;
  timeLabel: string;
  accent: "green" | "coral" | "yellow";
}

export interface FieldErrors {
  [fieldId: string]: string;
}

export const emptyProfileDraft = (): ProfileDraft => ({
  nickname: "",
  school: "",
  major: "",
  grade: "",
  skills: [],
  collaborationScenarios: [],
  rolePreference: "",
  hoursPerWeek: 6,
  bio: "",
  visibility: false,
  version: 0,
});

export const emptyProjectDraft = (): ProjectDraft => ({
  id: "",
  title: "",
  description: "",
  direction: "",
  competition: "",
  stage: "IDEA",
  teamInfo: "",
  status: "DRAFT",
  version: 0,
  publishedAt: null,
  roles: [
    {
      name: "",
      skills: [],
      headcount: 1,
      hoursPerWeek: 6,
      description: "",
      status: "OPEN",
    },
  ],
});
