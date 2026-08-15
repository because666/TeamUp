# TeamUp 页面与状态规范

> Status: Proposed<br>
> Owner: 角色 A<br>
> Reviewer: 角色 B（接口、安全与技术可行性）<br>
> Last Updated: 2026-08-15

## 1. 范围与约定

本文详细规定 P0 首条纵向切片页面。需求真值来自 [PRD](PRD.md)，接口和数据映射分别引用 [API_CONTRACT.md](../architecture/API_CONTRACT.md) 与 [DATA_MODEL.md](../architecture/DATA_MODEL.md)。本文中的 `GAP-*` 是待评审提案，不是已确认 API/schema。

命令控件在提交期间保持稳定尺寸并显示进行中状态；客户端防重复只改善体验，服务端仍必须执行鉴权、幂等、版本和状态校验。

## 2. 全局页面状态

| State | 展示 | 允许操作 |
| --- | --- | --- |
| `initial` | 稳定页面骨架，不显示假数据 | 返回或等待初始化 |
| `loading` | 与最终结构一致的加载状态 | 返回；不重复加载 |
| `ready` | 服务端确认内容或可编辑表单 | 当前页面正常命令 |
| `empty` | 明确无数据原因和一个主命令 | 创建/完善/返回 |
| `submitting` | 原内容保留，主命令锁定并显示进度 | 必要时取消导航，不重复提交 |
| `validation_error` | 字段内错误 + 页面错误摘要 | 修改并再次提交 |
| `network_error` | 不改变已确认状态，保留安全输入 | 重试或返回 |
| `unauthenticated` | 会话失效说明 | 重新登录 |
| `forbidden` | 无权操作，不泄露额外资源信息 | 返回安全页面 |
| `conflict` | 远程版本已变化 | 重新加载；不静默覆盖 |
| `success` | 服务端确认的结果与下一步 | 查看结果或继续任务 |

所有错误展示 `requestId` 的可复制短引用（若服务端返回），但不显示令牌、内部异常、微信凭证或数据库信息。

## 3. `S-AUTH-01` 登录与同意

目标：完成 `AUTH-001`，明确记录同意版本并建立平台会话。

页面内容：

| Element | Requirement | Data / Contract |
| --- | --- | --- |
| 产品名与登录标题 | 第一视口明确是 TeamUp 登录 | 静态产品内容 |
| 服务条款链接 | 可在登录前打开；展示版本/生效日期 | `GAP-AUTH-01` |
| 隐私政策链接 | 可在登录前打开；展示版本/生效日期 | `GAP-AUTH-01` |
| 同意复选框 | 默认未选；不能用预选或仅文案视为同意 | `User.consent_version` |
| 微信登录命令 | 未同意时禁用；提交中防重复 | `API-AUTH-01` |
| 错误区 | 区分用户取消、微信凭证失败、网络和服务端拒绝 | 通用错误 envelope |

状态要求：

- `initial/loading`：只初始化条款版本和本地会话状态，不提前获取微信凭证。
- `submitting`：一次性凭证只发送一次；重试必须重新获取。
- `success`：只依据服务端会话与名片状态导航。
- 用户拒绝/关闭：保持 Guest，不显示“登录成功”或创建正式账号。

## 4. `S-PROF-01` 能力名片编辑

目标：完成 `PROF-001/002`，建立用于项目协作的结构化资料，并让公开选择保持显式。

### 4.1 字段

以下必填规则是角色 A 的产品提案，角色 B 评审存储和校验可行性后再进入契约。

| Field ID | 页面字段 | Proposed Rule | API / Data Mapping | Visibility |
| --- | --- | --- | --- | --- |
| `PF-NICKNAME` | 昵称 | 必填；长度上限待契约确认 | `Profile.nickname` | 用户选择公开后可见 |
| `PF-SCHOOL` | 院校 | 必填；规范文本/选项方案待定 | `Profile.school` | 公开名片可见 |
| `PF-MAJOR` | 专业 | 必填 | `Profile.major` | 公开名片可见 |
| `PF-GRADE` | 年级 | 必填；受控枚举 | `Profile.grade` | 公开名片可见 |
| `PF-SKILLS` | 技能 | 至少 1 项；受控标签优先 | `ProfileSkill -> Skill` | 公开名片可见 |
| `PF-EXPERIENCE` | 项目/赛事/科研经历 | 可选；每项保留来源与认证状态 | `Experience` | 用户逐项确认公开范围，能力待补 |
| `PF-SCENARIO` | 合作场景 | 至少 1 项；受控枚举 | `GAP-PROF-02` | 用于发现/匹配，公开范围待审 |
| `PF-ROLE-PREF` | 队长/队员偏好 | 必填；允许“均可” | `GAP-PROF-02` | 用于发现/匹配 |
| `PF-HOURS` | 每周投入时间 | 必填；非负且范围待确认 | `Availability.hours_per_week` | 默认内部 |
| `PF-TIME-SLOTS` | 可用时段 | 可选但建议；结构化 | `Availability.time_slots` | 默认内部 |
| `PF-BIO` | 简介 | 可选；纯文本；AI 草稿不得自动覆盖 | `Profile.bio` | 公开名片可见 |
| `PF-VISIBILITY` | 进入人才大厅 | 默认关闭，用户显式开启 | `Profile.visibility` | 控制公开 |
| `PF-VERSION` | 版本 | 不向用户编辑，用于冲突检测 | `Profile.version` | Internal |

### 4.2 页面动作与状态

- 初次进入调用 `API-PROF-01`。`404/empty` 的精确契约属于 `GAP-PROF-01`，前端不能把任意加载失败当作空资料。
- 保存调用 `API-PROF-02`，请求必须带版本或等效条件；保存成功后使用服务端返回值替换本地已确认快照。
- 开启公开前展示将公开的字段摘要；联系方式不在此页收集或公开。
- `validation_error` 保留输入并定位问题；`conflict` 提供重新加载，不自动覆盖；`network_error` 保留本地草稿。
- 未保存离开必须确认；会话失效后的恢复草稿不包含 token、微信标识或他人非公开资料。

## 5. `S-ME-01` 与 `S-PROJ-LIST-01`

### `S-ME-01` 我的工作台

按任务优先级展示：名片完成度/可见性、我的项目摘要、邀请入口、账户与隐私。完成度必须由明确字段计算或服务端返回，不使用模糊 AI 评分。

### `S-PROJ-LIST-01` 我的项目

| State | Content | Primary Command |
| --- | --- | --- |
| loading | 列表结构加载状态 | 无 |
| empty | “还没有项目草稿” | 创建项目 |
| ready | 按 `DRAFT/PUBLISHED/CLOSED` 展示自己的项目 | 创建项目；进入管理 |
| network_error | 保留最后已确认快照并标记可能过期 | 重试 |

当前 `API-DISC-01 GET /projects` 定义为项目大厅，未定义“我的项目”查询语义，登记为 `GAP-PROJ-03`。不得用公开大厅接口猜测 owner 的草稿。

## 6. `S-PROJ-01` 项目与岗位编辑

目标：保存项目草稿和至少一个开放岗位，为 `PROJ-001` 发布做准备。

### 6.1 项目字段

| Field ID | 页面字段 | Proposed Rule | API / Data Mapping |
| --- | --- | --- | --- |
| `PJ-TITLE` | 项目标题 | 必填；纯文本；长度待契约 | `Project.title` |
| `PJ-DESCRIPTION` | 项目简介 | 必填；首版纯文本 | `Project.description` |
| `PJ-DIRECTION` | 项目方向 | 必填；受控选项 | `Project.direction` |
| `PJ-COMPETITIONS` | 适配赛事 | 可多选/补充文本，规范方案待定 | `GAP-PROJ-01` |
| `PJ-STAGE` | 项目阶段 | 必填；受控枚举 | `Project.stage` |
| `PJ-TEAM` | 现有团队信息 | 可选；区分用户填写与已认证 | `GAP-PROJ-01` |
| `PJ-STATUS` | 草稿/已发布/已关闭 | 只读，服务端状态 | `Project.status` |
| `PJ-VERSION` | 版本 | 只读，用于乐观锁 | `Project.version` |

### 6.2 岗位字段

| Field ID | 页面字段 | Proposed Rule | API / Data Mapping |
| --- | --- | --- | --- |
| `ROLE-NAME` | 岗位名称 | 必填 | `ProjectRole.name` |
| `ROLE-SKILLS` | 所需技能 | 至少 1 项；标记 required/importance | `ProjectRoleSkill -> Skill` |
| `ROLE-HEADCOUNT` | 招募人数 | 必填整数，`> 0` | `ProjectRole.headcount` |
| `ROLE-AVAILABILITY` | 投入时间 | 必填，结构需与名片可比较 | `ProjectRole.availability_requirement` |
| `ROLE-DESCRIPTION` | 岗位说明 | 可选；首版纯文本 | `GAP-PROJ-01` |
| `ROLE-STATUS` | 开放/关闭 | 新建默认开放提案 | `ProjectRole.status` |

### 6.3 保存行为

- 新草稿第一次保存调用 `API-PROJ-01`；之后调用 `API-PROJ-03`。
- 岗位是随项目 DTO 嵌套保存还是使用独立端点尚未定义，属于 `GAP-PROJ-01`；前端 mock 不得假装某一种已经确认。
- 保存中锁定同一保存命令，但允许继续查看；保存完成前离开必须确认。
- `409` 显示版本冲突；`403` 退出编辑权限；服务端字段错误映射到稳定 Field ID。
- 本地自动保存只能作为恢复草稿，不显示“已保存到云端”，也不能生成假资源 ID。

## 7. `S-PROJ-02/03` 发布预览与结果

### `S-PROJ-02` 发布预览

只显示服务端最后成功保存的项目快照，并单独标记尚未保存的本地修改。发布条件：项目必填项完整、至少一个 `OPEN` 岗位、每个开放岗位人数大于 0，当前用户是 owner，项目状态为 `DRAFT`。

页面包含：项目摘要、岗位列表、公开后可见范围、缺失项、返回编辑和发布命令。发布调用 `API-PROJ-04`；客户端重复提交防护不能替代服务端状态检查。

### `S-PROJ-03` 发布结果/项目详情

- `success` 必须来自服务端 `PUBLISHED` 状态；展示标题、状态、发布时间和公开预览。
- 响应丢失或状态不确定时调用 `API-PROJ-02`，不得直接显示成功。
- 主要命令为“查看项目”，次要命令为“继续管理”；返回进入我的项目列表。
- 已发布项目再次进入发布地址时直接恢复详情，不重复调用发布。
- 公共详情的每个开放岗位使用稳定 `roleId` 作为操作目标；非 owner 可点击“申请交换联系方式”，owner 查看自己的项目时不显示该动作。
- 申请成功显示 `PENDING` 状态并提供“查看联系请求”入口；不得显示“会话已建立”或在未同意时展示项目方联系方式。

发布条件、返回 DTO 与稳定错误码尚未完整定义，属于 `GAP-PROJ-02/04`。

## 8. `S-CONTACT-SET-01` 私有联系名片设置

目标：让用户维护专门用于双方同意交换的私有联系方式，不把联系方式混入公开能力名片。

| Field ID | 字段 | 规则 | 可见性 |
| --- | --- | --- | --- |
| `CT-WECHAT` | 微信号 | 可选；6..20 字符，字母开头，仅字母、数字、连字符和下划线 | 仅本人；交换接受后对方 |
| `CT-QQ` | QQ | 可选；5..12 位数字 | 仅本人；交换接受后对方 |
| `CT-EMAIL` | 邮箱 | 可选；5..254 字符，服务端校验基础邮箱格式 | 仅本人；交换接受后对方 |
| `CT-VERSION` | 版本 | 服务端乐观锁；首次保存为 1 | 仅本人/服务端 |

- 三种方式至少填写一种，每种类型最多一条；P0 不收集手机号。
- 进入页面调用 `API-CONTACT-CARD-01`；保存调用 `API-CONTACT-CARD-02`，只有服务端返回后显示“已保存”。
- 页面固定显示“默认不公开，仅在双方同意后交换”，不提供“公开到大厅”开关。
- `409 VERSION_CONFLICT` 要求重新加载，不覆盖其他设备保存的联系名片；离开未保存内容前确认。

## 9. `S-CONTACT-01/02` 联系请求列表与详情

`S-CONTACT-01` 是一级“联系”页面。第一层分段为“联系方式 / 项目邀请”，每个分段内再按“收到 / 发出”切换，避免把申请类型和方向混在同一级。联系方式交换列表调用 `API-CONTACT-REQ-02`，每个条目展示项目、岗位、对方昵称、状态和创建时间，不在列表预加载未接受请求的联系方式。项目邀请调用 `API-TEAM-04`，收到的待处理邀请提供“接受邀请 / 拒绝”，发出列表用于查看对方处理状态。

| 状态 | 收到的请求 | 发出的请求 | 联系方式展示 |
| --- | --- | --- | --- |
| `PENDING` | “同意交换”“拒绝” | “取消申请” | 不显示 |
| `ACCEPTED` | 状态“已同意” | 状态“对方已同意” | 展示对方微信号/QQ/邮箱及逐项复制按钮 |
| `REJECTED` | 状态“已拒绝” | 状态“对方已拒绝” | 不显示 |
| `CANCELLED` | 状态“对方已取消” | 状态“已取消” | 不显示 |

- 创建申请使用 `API-CONTACT-REQ-01`，请求体只含 `projectId` 和 `roleId`；客户端不得提交 recipient ID。
- 同意、拒绝、取消分别使用 `API-CONTACT-REQ-03/04/05`。按钮在请求中禁用，失败后恢复并保留可重试状态。
- 接收方没有联系名片时，同意动作返回 `CONTACT_CARD_REQUIRED` 并引导到 `S-CONTACT-SET-01`；申请人没有联系名片时不能创建申请。
- `401` 进入重新登录；无权或不可见请求统一显示安全空状态；拉黑、项目关闭、岗位关闭/满员等冲突显示服务端稳定错误，不伪造成功。
- 复制仅由用户点击触发；成功提示不重复显示完整联系方式值，剪贴板能力失败时保留可选择文本。
- 接受邀请调用 `API-TEAM-02`，成功后展示已加入项目；拒绝调用 `API-TEAM-03`。邀请过期、项目关闭、岗位关闭/满员和重复处理必须呈现服务端确定状态，不能由客户端自行判定成功。

## 10. 契约缺口清单

| Gap ID | Current Evidence | Needed Decision | Owner / Reviewer | Blocks |
| --- | --- | --- | --- | --- |
| `GAP-AUTH-01` | `API-AUTH-01` 未定义请求/响应 DTO | 同意版本、平台会话、名片完成状态和安全返回字段 | B / A | 登录联调 |
| `GAP-AUTH-02` | 无条款/隐私版本获取或失效约定 | 版本来源、拒绝同意、重新同意和错误码 | A + B | 首次登录联调 |
| `GAP-PROF-01` | `API-PROF-01/02` 无 DTO | 无名片语义、字段规则、完整状态、版本冲突和错误码 | B / A | 名片联调 |
| `GAP-PROF-02` | 数据模型无合作场景和角色偏好 | 字段枚举、公开范围、存储位置和匹配用途 | A + B | 名片契约确认 |
| `GAP-PROJ-01` | 项目/岗位写入 DTO 未定义 | 赛事、团队信息、岗位说明及嵌套/独立岗位写接口 | B / A | 项目编辑联调 |
| `GAP-PROJ-02` | `API-PROJ-04` 无发布前置/错误码 | 完整性、开放岗位、重复发布、冲突返回 | B / A | 发布联调 |
| `GAP-PROJ-03` | 只有公开项目列表 `API-DISC-01` | owner 的草稿/已发布/已关闭项目列表端点 | B / A | 我的项目联调 |
| `GAP-PROJ-04` | 项目详情 DTO 只有 `ProjectSummary` 示例 | owner 管理视图、公开视图、发布结果的字段边界 | B / A | 预览/结果联调 |
| `GAP-CONTACT-01` | 联系名片、交换申请和邀请列表已在当前任务分支实现，尚未由角色 B 评审并集成 | 复核 DTO、授权、披露边界、分页和微信端交互后转为 Confirmed | B / A | 联系与邀请联调 |

角色 A 可以基于本表设计界面和标注 mock；只有角色 B 更新 API/数据契约并完成跨角色评审后，才能把缺口标为 Confirmed。

## 11. 前端契约 Mock 规则

在工程初始化前只允许文档级 fixture，且每份数据必须带来源状态，避免把提案误认成真实接口：

```json
{
  "_fixture": true,
  "contractStatus": "PROPOSED_GAP",
  "gapIds": ["GAP-PROJ-01", "GAP-PROJ-02"],
  "screenState": "ready",
  "data": {
    "projectId": "fixture_project_01",
    "status": "DRAFT",
    "version": 1
  }
}
```

- fixture ID 必须使用 `fixture_` 前缀，不得看似生产 ID。
- fixture 只驱动页面状态，不模拟服务端权限成功、发布成功或组队成功。
- API DTO 确认后，fixture 必须从 OpenAPI 类型生成或接受契约测试；手写提案数据不能长期保留为第二套契约。

## 12. 页面验收矩阵

| Screen | Loading | Empty | Validation | Network | 401 | 403 | 409 | Success |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `S-AUTH-01` | Required | N/A | 同意未勾选 | Required | 重新登录 | 同意/账号限制说明 | N/A | 路由按资料状态 |
| `S-PROF-01` | Required | 新建表单 | Required | Required | 保留安全草稿后登录 | 返回我的 | Required | 服务端快照 |
| `S-PROJ-LIST-01` | Required | 创建项目 | N/A | Required | 重新登录 | 安全空状态 | N/A | 自有项目列表 |
| `S-PROJ-01` | Required | 新草稿 | Required | Required | 保留安全草稿后登录 | 退出编辑 | Required | 已保存版本 |
| `S-PROJ-02` | Required | 返回编辑 | 缺失项 | Required | 重新登录 | 退出管理 | Required | 发起发布 |
| `S-PROJ-03` | Required | N/A | N/A | 查询真实状态 | 重新登录 | 公开/安全返回 | N/A | `PUBLISHED` 详情 |
| `S-CONTACT-SET-01` | Required | 新建联系名片 | 至少一种有效方式 | Required | 保留安全草稿后登录 | 返回我的 | 重新加载版本 | 服务端快照 |
| `S-CONTACT-01/02` | Required | 按分段说明空状态 | N/A | Required | 重新登录 | 安全空状态 | 保留可重试动作 | 状态与披露范围一致 |

视觉稿和前端实现必须覆盖本矩阵，但截图不能替代接口、权限、重复提交和状态恢复测试。
