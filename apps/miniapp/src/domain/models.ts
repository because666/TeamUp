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
  id: string;
  name: string;
  skills: string[];
  headcount: number;
  hoursPerWeek: number;
  description: string;
  status: "OPEN" | "CLOSED";
}

export interface ProjectDraft {
  id: string;
  ownerId?: string;
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

export type ContactMethodType = "WECHAT" | "QQ" | "EMAIL";
export type ContactExchangeStatus = "PENDING" | "ACCEPTED" | "REJECTED" | "CANCELLED";
export type ContactExchangeBox = "SENT" | "RECEIVED";

export interface ContactMethod {
  type: ContactMethodType;
  value: string;
}

export interface ContactCard {
  methods: ContactMethod[];
  version: number;
  updatedAt?: string;
}

export interface ContactExchangeRequest {
  id: string;
  projectId: string;
  roleId: string;
  projectTitle: string;
  roleName: string;
  requesterUserId: string;
  recipientUserId: string;
  box: ContactExchangeBox;
  peerDisplayName: string;
  status: ContactExchangeStatus;
  peerContactCard: ContactCard | null;
  createdAt: string;
  respondedAt: string | null;
}

export type ProjectInvitationStatus = "PENDING" | "ACCEPTED" | "REJECTED" | "EXPIRED" | "CANCELLED";
export type ProjectInvitationBox = "SENT" | "RECEIVED";

export interface ProjectInvitationRecord {
  id: string;
  projectId: string;
  roleId: string;
  inviterUserId: string;
  inviteeUserId: string;
  status: ProjectInvitationStatus;
  expiresAt: string;
  createdAt: string;
  respondedAt: string | null;
}

export interface ProjectInvitation extends ProjectInvitationRecord {
  projectTitle: string;
  roleName: string;
  box: ProjectInvitationBox;
  peerDisplayName: string;
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
      id: "",
      name: "",
      skills: [],
      headcount: 1,
      hoursPerWeek: 6,
      description: "",
      status: "OPEN",
    },
  ],
});
