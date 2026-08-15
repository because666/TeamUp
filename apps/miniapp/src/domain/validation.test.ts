import { describe, expect, it } from "vitest";
import { emptyProfileDraft, emptyProjectDraft } from "./models";
import { isValid, validateContactCard, validateProfile, validateProject } from "./validation";

describe("profile validation", () => {
  it("reports every P0 required group on an empty profile", () => {
    const errors = validateProfile(emptyProfileDraft());

    expect(errors["PF-NICKNAME"]).toBeTruthy();
    expect(errors["PF-SCHOOL"]).toBeTruthy();
    expect(errors["PF-SKILLS"]).toBeTruthy();
    expect(errors["PF-SCENARIO"]).toBeTruthy();
    expect(errors["PF-ROLE-PREF"]).toBeTruthy();
  });

  it("accepts a complete profile draft", () => {
    const profile = emptyProfileDraft();
    Object.assign(profile, {
      nickname: "林同学",
      school: "示例大学",
      major: "计算机科学",
      grade: "大二",
      skills: ["TypeScript"],
      collaborationScenarios: ["竞赛"],
      rolePreference: "FLEXIBLE",
      hoursPerWeek: 8,
    });

    expect(isValid(validateProfile(profile))).toBe(true);
  });
});

describe("project validation", () => {
  it("does not allow publishing an incomplete project", () => {
    const errors = validateProject(emptyProjectDraft());

    expect(errors["PJ-TITLE"]).toBeTruthy();
    expect(errors["ROLE-1-NAME"]).toBeTruthy();
    expect(errors["ROLE-1-SKILLS"]).toBeTruthy();
  });

  it("accepts a project with one complete open role", () => {
    const project = emptyProjectDraft();
    Object.assign(project, {
      title: "校园协作项目",
      description: "通过结构化信息帮助同学找到合适的合作伙伴。",
      direction: "校园服务",
    });
    Object.assign(project.roles[0], {
      name: "前端开发",
      skills: ["Vue"],
      headcount: 1,
      hoursPerWeek: 6,
    });

    expect(isValid(validateProject(project))).toBe(true);
  });
});

describe("contact card validation", () => {
  it("requires at least one supported valid method", () => {
    expect(validateContactCard({ methods: [], version: 0 })["CT-METHODS"]).toBeTruthy();
    expect(validateContactCard({
      methods: [{ type: "WECHAT", value: "short" }],
      version: 0,
    })["CT-WECHAT"]).toBeTruthy();
  });

  it("accepts WeChat, QQ and email without collecting phone numbers", () => {
    expect(isValid(validateContactCard({
      methods: [
        { type: "WECHAT", value: "teamup_user" },
        { type: "QQ", value: "12345678" },
        { type: "EMAIL", value: "user@example.com" },
      ],
      version: 0,
    }))).toBe(true);
  });
});
