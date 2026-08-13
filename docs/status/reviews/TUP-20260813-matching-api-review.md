# TUP-20260813-matching-api 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/feature/TUP-20260813-matching-api`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-13

## 1. 评审范围

- `GET /api/v1/projects/{projectId}/matches?roleId=...` 岗位候选成员；
- `GET /api/v1/me/project-matches` 用户候选项目岗位；
- `RULE/match-v0.1` 分数、置信度、因素和缺失信息；
- required skill、时间段、项目/岗位状态、容量、成员和双向拉黑过滤；
- 项目 owner 授权、名片完成度和不透明 cursor；
- 进程内短期推荐快照的暂时性边界。

## 2. 角色 A 验收清单

| ID | 验收项 | 预期行为 | 角色 A 结论 |
| --- | --- | --- | --- |
| MATCH-A-001 | owner 候选成员 | 仅项目 owner 可按岗位查看公开候选 | TBD |
| MATCH-A-002 | 用户候选岗位 | 当前用户可查看开放项目岗位，结果按岗位粒度 | TBD |
| MATCH-A-003 | 硬约束 | required skill、时间段、满员、成员和拉黑目标不返回 | TBD |
| MATCH-A-004 | 解释结果 | 返回 score、confidence、因素、缺失信息和规则版本，不返回 rankingScore | TBD |
| MATCH-A-005 | 游标 | 首次签发 request ID，非法/跨上下文 cursor 明确失败 | TBD |
| MATCH-A-006 | 未完成资料 | 缺少名片或匹配偏好返回 `MATCH_PROFILE_INCOMPLETE` | TBD |
| MATCH-A-007 | 快照边界 | 接受当前进程内快照作为 Proposed 联调实现，不视为持久化推荐已完成 | TBD |
| MATCH-A-008 | 非目标 | 曝光、训练数据、模型重排和推荐表不在本任务 | TBD |

## 3. 角色 B 验证证据

- API 与 SQL/memory store 测试覆盖 owner、非 owner、公开状态、required skill、拉黑、匹配偏好、cursor 和未完成资料；
- `python -m pytest -ra`：60 passed，6 个 MySQL 专属测试因未配置 `TEAMUP_TEST_MYSQL_URL` 跳过；
- `python -m compileall -q app tests`：passed；
- `git diff --check`：passed；
- 真实 MySQL 匹配 API 查询：本轮未运行，待配置独立测试库补验；
- ADR-0005 仍为 Proposed，持久化推荐快照和曝光必须另行评审。

## 4. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| Finding ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |

评审通过前不得合入 `main`。重点确认岗位摘要字段、方向偏好语义、时间段硬约束和进程内快照的临时性质。
