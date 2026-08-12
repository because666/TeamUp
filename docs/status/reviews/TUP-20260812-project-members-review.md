# TUP-20260812-project-members 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/feature/TUP-20260812-project-members`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-12

## 1. 评审范围

- 岗位响应新增 `filledCount` 和 `remainingCount`；
- `GET /api/v1/projects/{projectId}/members` 的展示字段、空状态和权限错误；
- 一个用户在同一项目最多占一个岗位；
- 项目关闭后保留成员和容量，但阻止新增；
- 本任务不提供公共成员写接口，后续只能通过接受邀请形成成员。

## 2. 角色 A 验收清单

| ID | 验收项 | 预期行为 | 角色 A 结论 |
| --- | --- | --- | --- |
| PM-A-001 | 容量展示 | 岗位返回总人数、已加入人数和剩余人数 | TBD |
| PM-A-002 | 成员列表权限 | 仅 owner 或有效成员可读，普通用户返回 `403` | TBD |
| PM-A-003 | 成员最小字段 | 只返回 opaque 用户 ID、岗位、状态和加入时间 | TBD |
| PM-A-004 | 入队入口 | 无直接添加 HTTP 接口；后续必须通过邀请接受事务 | TBD |
| PM-A-005 | 项目内唯一成员 | 同一用户在一个项目不能同时占多个岗位 | TBD |
| PM-A-006 | 关闭项目 | 保留现有成员，但不再允许新增 | TBD |
| PM-A-007 | 前置依赖 | 本分支堆叠在匹配偏好提交 `2edb4b1` 上，需按顺序评审 | TBD |

## 3. 角色 B 验证证据

- Memory API 和 SQLite repository 覆盖 owner、成员、非成员、未认证权限；
- 重复成员、草稿/关闭项目、关闭岗位、满员和跨项目岗位均由服务端或数据库拒绝；
- 真实 MySQL 并发争夺最后一个名额的结果以任务文件最终记录为准；
- migration upgrade/downgrade、ORM schema 和完整回归结果以任务文件为准。

## 4. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| Finding ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |

评审通过前不得合入 `main`。邀请、成员退出/踢出/换岗和 owner 转移必须使用后续独立任务，不得在评审时静默扩展本任务范围。
