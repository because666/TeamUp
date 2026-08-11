import type {
  DiscoveryProject,
  FixtureEnvelope,
  ProfileDraft,
  ProjectDraft,
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

export const cloneProfile = (profile: ProfileDraft): ProfileDraft =>
  JSON.parse(JSON.stringify(profile)) as ProfileDraft;

export const cloneProject = (project: ProjectDraft): ProjectDraft =>
  JSON.parse(JSON.stringify(project)) as ProjectDraft;
