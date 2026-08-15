import type { ContactCard, FieldErrors, ProfileDraft, ProjectDraft } from "./models";

const isBlank = (value: string) => value.trim().length === 0;

export function validateProfile(profile: ProfileDraft): FieldErrors {
  const errors: FieldErrors = {};

  if (isBlank(profile.nickname)) errors["PF-NICKNAME"] = "请填写昵称";
  if (isBlank(profile.school)) errors["PF-SCHOOL"] = "请填写院校";
  if (isBlank(profile.major)) errors["PF-MAJOR"] = "请填写专业";
  if (isBlank(profile.grade)) errors["PF-GRADE"] = "请选择年级";
  if (profile.skills.length === 0) errors["PF-SKILLS"] = "至少选择一项技能";
  if (profile.collaborationScenarios.length === 0) {
    errors["PF-SCENARIO"] = "至少选择一种合作场景";
  }
  if (!profile.rolePreference) errors["PF-ROLE-PREF"] = "请选择合作角色偏好";
  if (!Number.isInteger(profile.hoursPerWeek) || profile.hoursPerWeek < 1) {
    errors["PF-HOURS"] = "每周投入时间至少为 1 小时";
  }
  if (profile.nickname.trim().length > 24) {
    errors["PF-NICKNAME"] = "昵称暂不超过 24 个字符";
  }
  if (profile.bio.length > 240) errors["PF-BIO"] = "简介暂不超过 240 个字符";

  return errors;
}

export function validateProject(project: ProjectDraft): FieldErrors {
  const errors: FieldErrors = {};

  if (isBlank(project.title)) errors["PJ-TITLE"] = "请填写项目标题";
  if (isBlank(project.description)) errors["PJ-DESCRIPTION"] = "请填写项目简介";
  if (isBlank(project.direction)) errors["PJ-DIRECTION"] = "请选择项目方向";
  if (isBlank(project.stage)) errors["PJ-STAGE"] = "请选择项目阶段";
  if (project.title.trim().length > 48) errors["PJ-TITLE"] = "项目标题暂不超过 48 个字符";
  if (project.description.length > 600) {
    errors["PJ-DESCRIPTION"] = "项目简介暂不超过 600 个字符";
  }

  const openRoles = project.roles.filter((role) => role.status === "OPEN");
  if (openRoles.length === 0) errors["ROLE-LIST"] = "至少保留一个开放岗位";

  project.roles.forEach((role, index) => {
    const prefix = `ROLE-${index + 1}`;
    if (isBlank(role.name)) errors[`${prefix}-NAME`] = "请填写岗位名称";
    if (role.skills.length === 0) errors[`${prefix}-SKILLS`] = "至少选择一项岗位技能";
    if (!Number.isInteger(role.headcount) || role.headcount < 1) {
      errors[`${prefix}-HEADCOUNT`] = "招募人数至少为 1";
    }
    if (!Number.isInteger(role.hoursPerWeek) || role.hoursPerWeek < 1) {
      errors[`${prefix}-HOURS`] = "每周投入时间至少为 1 小时";
    }
  });

  return errors;
}

export function validateContactCard(card: ContactCard): FieldErrors {
  const errors: FieldErrors = {};
  if (card.methods.length === 0) errors["CT-METHODS"] = "请至少填写一种联系方式";
  const types = card.methods.map((method) => method.type);
  if (new Set(types).size !== types.length) errors["CT-METHODS"] = "每种联系方式只能填写一次";
  card.methods.forEach((method) => {
    const value = method.value.trim();
    if (method.type === "WECHAT" && !/^[A-Za-z][A-Za-z0-9_-]{5,19}$/.test(value)) {
      errors["CT-WECHAT"] = "微信号需为 6-20 位，并以字母开头";
    }
    if (method.type === "QQ" && !/^[1-9][0-9]{4,11}$/.test(value)) {
      errors["CT-QQ"] = "QQ 需为 5-12 位数字";
    }
    if (
      method.type === "EMAIL"
      && !/^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/.test(value)
    ) {
      errors["CT-EMAIL"] = "请填写有效邮箱地址";
    }
  });
  return errors;
}

export const isValid = (errors: FieldErrors): boolean => Object.keys(errors).length === 0;
