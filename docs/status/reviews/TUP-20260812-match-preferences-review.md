# TUP-20260812-match-preferences 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/feature/TUP-20260812-match-preferences`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-12

## 1. 评审范围

- `GET/PUT /api/v1/me/match-preferences` 的表单字段、空状态、错误处理和版本冲突；
- 项目/岗位新增 `collaborationScenarios`、`requiredSkills`、`requiredAvailabilitySlots` 和 `collaborationRole`；
- 旧前端省略新字段时的兼容行为；
- 历史岗位技能全部迁移为 bonus、历史岗位协作身份迁移为 `MEMBER`；
- 当前任务不发布匹配列表、推荐快照、经历、成员容量和拉黑模块。

## 2. 角色 A 验收清单

| ID | 验收项 | 预期行为 | 角色 A 结论 |
| --- | --- | --- | --- |
| MP-A-001 | 偏好未创建 | GET 返回 `data: null` 和 `meta.state: INCOMPLETE` | TBD |
| MP-A-002 | 方向偏好 | 最多 10 项；当前仅校验非空、64 字符和去重，受控词表待角色 A 提供 | TBD |
| MP-A-003 | 时间段 | P0 固定 `Asia/Shanghai`；同星期不允许重叠 | TBD |
| MP-A-004 | 乐观锁 | 首次 PUT 使用 `version=0`；旧版本返回 `409 VERSION_CONFLICT` | TBD |
| MP-A-005 | 必需技能 | `requiredSkills` 必须是 `skills` 子集；历史和新建省略时均为空 | TBD |
| MP-A-006 | 旧前端更新 | 省略新字段时保留原值；移除技能时只移除不再存在的 required | TBD |
| MP-A-007 | 协作身份 | `LEADER/MEMBER/FLEXIBLE`；历史岗位为 `MEMBER` | TBD |
| MP-A-008 | 协作场景 | 项目创建省略时为空，更新省略时保留；受控词表待角色 A 提供 | TBD |

## 3. 角色 B 验证证据

- 内存 API、SQLite repository、迁移 upgrade/downgrade、历史数据升级和 OpenAPI schema 已纳入自动化测试；
- 未认证访问、重复方向、重叠时间段、required 非子集和 stale version 均有拒绝用例；
- 真实 MySQL 验证结果以任务文件最终记录为准；
- Reviewed Commit 在角色 B 完成提交后填写。

## 4. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| Finding ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |

角色 A 批准后，角色 B 才能申请将本分支集成到 `main`；ADR-0005 的其余推荐快照与匹配列表决策不因本次局部评审自动变为 Accepted。
