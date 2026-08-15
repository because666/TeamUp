import type {
  ContactExchangeRequest,
  DiscoveryProject,
  FixtureEnvelope,
  ProfileDraft,
  ProjectDraft,
  ProjectInvitation,
} from "./models";

let fixtureRequestSequence = 0;

export function fixtureEnvelope<T>(data: T, gapIds: string[]): FixtureEnvelope<T> {
  fixtureRequestSequence += 1;
  return {
    _fixture: true,
    contractStatus: "PROPOSED_GAP",
    gapIds: [...gapIds],
    requestId: `fixture_request_${fixtureRequestSequence}`,
    data,
  };
}

export const discoveryProjects: DiscoveryProject[] = [
  {
    id: "fixture_project_public_01",
    title: "校园低碳路线规划",
    direction: "绿色科技",
    stage: "原型验证",
    summary: "把校园出行数据转成可执行的减排建议，正在补充数据分析与产品设计能力。",
    skills: ["Python", "数据分析", "产品设计"],
    openRoleCount: 2,
    timeLabel: "每周 6-8 小时",
    accent: "green",
  },
  {
    id: "fixture_project_public_02",
    title: "非遗数字展陈工具",
    direction: "文化创意",
    stage: "方案设计",
    summary: "为校内非遗社团制作轻量展陈工具，需要视觉、前端和内容策划成员。",
    skills: ["UI 设计", "Vue", "内容策划"],
    openRoleCount: 3,
    timeLabel: "每周 4-6 小时",
    accent: "coral",
  },
  {
    id: "fixture_project_public_03",
    title: "实验室设备预约助手",
    direction: "校园服务",
    stage: "需求验证",
    summary: "减少设备预约冲突和空置时间，优先寻找熟悉调研与后端接口的同学。",
    skills: ["用户研究", "Java", "数据库"],
    openRoleCount: 2,
    timeLabel: "每周 5 小时",
    accent: "yellow",
  },
];

export const discoveryProjectDetails: ProjectDraft[] = [
  {
    id: "fixture_project_public_01",
    ownerId: "fixture_user_owner_01",
    title: "校园低碳路线规划",
    description: "把校园出行数据转成可执行的减排建议，正在补充数据分析与产品设计能力。",
    direction: "绿色科技",
    competition: "中国国际大学生创新大赛",
    stage: "PROTOTYPE",
    teamInfo: "现有成员负责校园调研与路线数据采集。",
    status: "PUBLISHED",
    version: 1,
    publishedAt: "2026-08-10T08:00:00Z",
    roles: [
      {
        id: "fixture_role_public_01_data",
        name: "数据分析",
        skills: ["Python", "数据分析"],
        headcount: 1,
        hoursPerWeek: 8,
        description: "整理出行数据并验证减排指标。",
        status: "OPEN",
      },
      {
        id: "fixture_role_public_01_product",
        name: "产品设计",
        skills: ["产品设计", "用户研究"],
        headcount: 1,
        hoursPerWeek: 6,
        description: "梳理使用流程并完成原型验证。",
        status: "OPEN",
      },
    ],
  },
  {
    id: "fixture_project_public_02",
    ownerId: "fixture_user_owner_02",
    title: "非遗数字展陈工具",
    description: "为校内非遗社团制作轻量展陈工具，需要视觉、前端和内容策划成员。",
    direction: "文化创意",
    competition: "大学生创新创业训练计划",
    stage: "IDEA",
    teamInfo: "已完成社团访谈和首批展品资料整理。",
    status: "PUBLISHED",
    version: 1,
    publishedAt: "2026-08-09T09:30:00Z",
    roles: [
      {
        id: "fixture_role_public_02_visual",
        name: "视觉设计",
        skills: ["UI 设计"],
        headcount: 1,
        hoursPerWeek: 5,
        description: "建立展陈页面的视觉规范。",
        status: "OPEN",
      },
      {
        id: "fixture_role_public_02_frontend",
        name: "前端开发",
        skills: ["Vue"],
        headcount: 1,
        hoursPerWeek: 6,
        description: "实现移动端展陈与内容浏览。",
        status: "OPEN",
      },
      {
        id: "fixture_role_public_02_content",
        name: "内容策划",
        skills: ["内容策划"],
        headcount: 1,
        hoursPerWeek: 4,
        description: "整理非遗故事和展品说明。",
        status: "OPEN",
      },
    ],
  },
  {
    id: "fixture_project_public_03",
    ownerId: "fixture_user_owner_03",
    title: "实验室设备预约助手",
    description: "减少设备预约冲突和空置时间，优先寻找熟悉调研与后端接口的同学。",
    direction: "校园服务",
    competition: "互联网+校内选拔",
    stage: "VALIDATION",
    teamInfo: "已联系两个实验室开展需求访谈。",
    status: "PUBLISHED",
    version: 1,
    publishedAt: "2026-08-08T03:20:00Z",
    roles: [
      {
        id: "fixture_role_public_03_research",
        name: "用户研究",
        skills: ["用户研究"],
        headcount: 1,
        hoursPerWeek: 5,
        description: "访谈师生并整理预约冲突场景。",
        status: "OPEN",
      },
      {
        id: "fixture_role_public_03_backend",
        name: "后端开发",
        skills: ["Java", "数据库"],
        headcount: 1,
        hoursPerWeek: 5,
        description: "设计预约规则与接口数据结构。",
        status: "OPEN",
      },
    ],
  },
];

export const initialFixtureContactRequests: ContactExchangeRequest[] = [
  {
    id: "fixture_contact_request_received_01",
    projectId: "fixture_project_owned_01",
    roleId: "fixture_role_owned_product",
    projectTitle: "校园创新项目",
    roleName: "产品设计",
    requesterUserId: "fixture_user_candidate_01",
    recipientUserId: "fixture_user_current_01",
    box: "RECEIVED",
    peerDisplayName: "周同学",
    status: "PENDING",
    peerContactCard: null,
    createdAt: "2026-08-15T06:30:00Z",
    respondedAt: null,
  },
  {
    id: "fixture_contact_request_accepted_01",
    projectId: "fixture_project_public_02",
    roleId: "fixture_role_public_02_frontend",
    projectTitle: "非遗数字展陈工具",
    roleName: "前端开发",
    requesterUserId: "fixture_user_current_01",
    recipientUserId: "fixture_user_owner_02",
    box: "SENT",
    peerDisplayName: "陈同学",
    status: "ACCEPTED",
    peerContactCard: {
      methods: [
        { type: "WECHAT", value: "fixture_owner_02" },
        { type: "EMAIL", value: "owner02@example.com" },
      ],
      version: 1,
      updatedAt: "2026-08-15T07:00:00Z",
    },
    createdAt: "2026-08-14T09:00:00Z",
    respondedAt: "2026-08-15T07:00:00Z",
  },
];

export const initialFixtureProjectInvitations: ProjectInvitation[] = [
  {
    id: "fixture_invitation_received_01",
    projectId: "fixture_project_public_02",
    roleId: "fixture_role_public_02_frontend",
    projectTitle: "非遗数字展陈工具",
    roleName: "前端开发",
    inviterUserId: "fixture_user_owner_02",
    inviteeUserId: "fixture_user_current_01",
    box: "RECEIVED",
    peerDisplayName: "陈同学",
    status: "PENDING",
    expiresAt: "2026-08-22T09:30:00Z",
    createdAt: "2026-08-15T09:30:00Z",
    respondedAt: null,
  },
  {
    id: "fixture_invitation_sent_01",
    projectId: "fixture_project_owned_01",
    roleId: "fixture_role_owned_product",
    projectTitle: "校园创新项目",
    roleName: "产品设计",
    inviterUserId: "fixture_user_current_01",
    inviteeUserId: "fixture_user_candidate_02",
    box: "SENT",
    peerDisplayName: "林同学",
    status: "ACCEPTED",
    expiresAt: "2026-08-20T07:00:00Z",
    createdAt: "2026-08-13T07:00:00Z",
    respondedAt: "2026-08-14T10:00:00Z",
  },
];

export const cloneProfile = (profile: ProfileDraft): ProfileDraft =>
  JSON.parse(JSON.stringify(profile)) as ProfileDraft;

export const cloneProject = (project: ProjectDraft): ProjectDraft =>
  JSON.parse(JSON.stringify(project)) as ProjectDraft;

export const cloneContactRequests = (
  requests: ContactExchangeRequest[],
): ContactExchangeRequest[] => JSON.parse(JSON.stringify(requests)) as ContactExchangeRequest[];

export const cloneProjectInvitations = (
  invitations: ProjectInvitation[],
): ProjectInvitation[] => JSON.parse(JSON.stringify(invitations)) as ProjectInvitation[];
