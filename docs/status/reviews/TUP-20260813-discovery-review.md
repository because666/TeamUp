# TUP-20260813-discovery 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/feature/TUP-20260813-discovery`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-13

## 1. 评审范围

- `GET /api/v1/projects` 项目大厅筛选和游标分页；
- `GET /api/v1/profiles` 人才大厅筛选和公开字段；
- `GET /api/v1/profiles/{profileId}` 公开名片详情；
- `GET /api/v1/me/projects` 当前用户项目列表；
- 双向拉黑、账号状态和公开状态过滤；
- Guest 访问暂不开放的保守假设。

## 2. 角色 A 验收清单

| ID | 验收项 | 预期行为 | 角色 A 结论 |
| --- | --- | --- | --- |
| DISC-A-001 | 项目筛选 | 方向、赛事、技能、阶段和 PUBLISHED 状态筛选生效 | TBD |
| DISC-A-002 | 项目分页 | 最新发布时间/ID 稳定倒序，无重复或遗漏 | TBD |
| DISC-A-003 | 人才公开 | 只返回明确公开且账号 ACTIVE 的名片 | TBD |
| DISC-A-004 | 人才筛选 | 技能、匹配方向、合作角色和投入时间筛选生效 | TBD |
| DISC-A-005 | 公开详情 | 非公开、拉黑或本人资源统一不可见 | TBD |
| DISC-A-006 | 我的项目 | 只返回当前用户项目，可按 DRAFT/PUBLISHED/CLOSED 筛选 | TBD |
| DISC-A-007 | Guest 策略 | 评审是否接受当前阶段要求登录的保守假设 | TBD |
| DISC-A-008 | 非目标 | 推荐 API、曝光、搜索引擎、管理员治理不在本任务 | TBD |

## 3. 角色 B 验证证据

- API、memory/SQL 查询测试覆盖公开状态、筛选、分页、拉黑和 owner 边界；
- 最新全量验证为 80 passed（真实 MySQL 8.4.11），详见对应任务文件；角色 A 需独立核对。
- `python -m compileall -q app tests`：passed；
- `git diff --check`：passed；
- MySQL 真实连接测试：本任务未运行，待配置独立测试数据库后补验。

## 4. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| Finding ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |

评审通过前不得合入 `main`。重点确认 Guest 是否应开放公开摘要、`direction` 对匹配偏好的语义、公开名片字段和筛选精确匹配规则。
