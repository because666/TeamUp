# TeamUp 当前状态

> Status: Confirmed<br>
> Snapshot Branch: `main`<br>
> Remote Baseline: `167edd5`<br>
> Last Updated: 2026-08-14 by 角色 B（集成交接）

本文件只记录已合并或正在明确交接的聚合状态，不记录逐步开发日志。单个任务的实时进展见 `tasks/`。

## 1. 项目阶段

`main` 仍处于文档与工程基线建设阶段；可运行的 UniApp 前端、FastAPI 后端和 P0 真实 API adapter 已在独立任务分支形成，正通过 `role-b/feature/TUP-20260814-p0-integration` 进行组合验证，尚未集成到 `main`。

## 2. 当前能力

| 范围 | 状态 | 说明 |
| --- | --- | --- |
| 原始需求 | Available | 两份 PDF 已保留在仓库根目录 |
| 产品规范 | Ready for review | 已转为带需求 ID、验收标准和范围边界的 Markdown |
| AI 协作治理 | Ready for review | 根 AGENTS、双人工作流、任务/交接模板已建立 |
| 技术架构 | Proposed | 模块化单体和契约基线待双方评审 |
| 前端工程 | Ready for review | 任务分支已完成 UniApp P0 页面、fixture、真实 API adapter、测试与构建；尚未集成 `main` |
| 后端工程 | Ready for review | FastAPI、MySQL/Alembic、认证、项目、匹配、协作、安全与可观测性堆叠任务已实现并验证；尚未集成 `main` |
| P0 前后端集成 | In progress | 独立集成分支正在组合两端并复跑测试、构建和 OpenAPI 契约检查 |
| 部署环境 | Not started | 腾讯云方向已知，具体拓扑未确定 |

## 3. 活跃任务

| Task ID | Owner | Area | Status | Working location | Record |
| --- | --- | --- | --- | --- | --- |
| TUP-20260810-docs-baseline | 角色 A | 文档、AI 协作与推荐策略基线 | Ready for Review | `role-a/docs/TUP-20260810-docs-baseline` | [任务记录](tasks/TUP-20260810-docs-baseline.md) |
| TUP-20260810-role-b-review | 角色 B | 文档、后端可行性、安全与协作规则核对 | Pending | `origin/role-a/docs/TUP-20260810-docs-baseline` | [评审记录](reviews/TUP-20260810-role-b-review.md) |
| TUP-20260810-role-a-product-foundation | 角色 A | 用户流程、信息架构与页面状态规范 | Ready for Review | `role-a/docs/TUP-20260810-role-a-product-foundation` | [任务记录](tasks/TUP-20260810-role-a-product-foundation.md) |
| TUP-20260810-backend-frontend-integration | 角色 B | 前后端契约、mock、联调与交付流程 | Proposed | `role-a/docs/TUP-20260810-role-a-product-backend` | [任务记录](tasks/TUP-20260810-backend-frontend-integration.md) |
| TUP-20260811-fastapi-backend | 角色 B | FastAPI 框架决策、完整后端 PRD 与后端基线 | In Progress | `role-b/feature/TUP-20260811-fastapi-backend` | [任务记录](tasks/TUP-20260811-fastapi-backend.md) |
| TUP-20260811-frontend-foundation | 角色 A | UniApp 微信小程序工程与 P0 页面骨架 | Ready for Review | `role-a/feature/TUP-20260811-frontend-foundation` | [任务记录](tasks/TUP-20260811-frontend-foundation.md) |
| TUP-20260811-match-v0-1 | 角色 B | 可解释规则匹配引擎与 golden tests | Ready for Review | `role-b/feature/TUP-20260811-match-v0-1` | [任务记录](tasks/TUP-20260811-match-v0-1.md) |
| TUP-20260811-match-api-data-contract | 角色 B | 匹配 API、分页与数据扩展契约 | Ready for Review | `role-b/docs/TUP-20260811-match-api-data-contract` | [任务记录](tasks/TUP-20260811-match-api-data-contract.md) |
| TUP-20260812-match-preferences | 角色 B | 匹配偏好与岗位匹配字段 | Ready for Review | `role-b/feature/TUP-20260812-match-preferences` | [任务记录](tasks/TUP-20260812-match-preferences.md) |
| TUP-20260812-project-members | 角色 B | 项目成员与岗位容量 | Ready for Review | `role-b/feature/TUP-20260812-project-members` | [任务记录](tasks/TUP-20260812-project-members.md) |
| TUP-20260812-user-blocks | 角色 B | 用户拉黑与安全过滤 | Ready for Review | `role-b/feature/TUP-20260812-user-blocks` | [任务记录](tasks/TUP-20260812-user-blocks.md) |
| TUP-20260812-project-invitations | 角色 B | 项目岗位邀请与接受事务 | Ready for Review | `role-b/feature/TUP-20260812-project-invitations` | [任务记录](tasks/TUP-20260812-project-invitations.md) |
| TUP-20260812-conversations-messages | 角色 B | 双人会话与文本消息 | Ready for Review | `role-b/feature/TUP-20260812-conversations-messages` | [任务记录](tasks/TUP-20260812-conversations-messages.md) |
| TUP-20260814-frontend-api-adapter | 角色 B（跨角色集成） | 微信登录与 P0 真实 API adapter | Ready for Review | `role-b/feature/TUP-20260814-frontend-api-adapter` | [任务记录](tasks/TUP-20260814-frontend-api-adapter.md) |
| TUP-20260814-project-put-compat | 角色 B | 微信兼容项目 PUT 更新路由 | Ready for Review | `role-b/feature/TUP-20260814-project-put-compat` | [任务记录](tasks/TUP-20260814-project-put-compat.md) |
| TUP-20260814-p0-integration | 角色 B | P0 前后端组合验证与交接 | In Progress | `role-b/feature/TUP-20260814-p0-integration` | [任务记录](tasks/TUP-20260814-p0-integration.md) |

完整的堆叠任务与评审入口见 [任务目录](tasks/README.md)。集成分支由角色 B 唯一编辑；角色 A 通过独立评审文件给出结论，双方不得同时修改高冲突契约。

## 4. 关键决策

| ADR | 事项 | Owner | 阻塞内容 |
| --- | --- | --- | --- |
| [ADR-0001](../decisions/ADR-0001-backend-framework.md) | FastAPI | 角色 B已确认，角色 A评审 | 状态：Accepted；具体版本和工具链待初始化验证 |
| [ADR-0002](../decisions/ADR-0002-mvp-ai-scope.md) | 规则算法 P0 + 自训练轻量模型 P1 | 角色 A已确认，角色 B实施前评审 | 状态：Accepted；模型启用门槛待数据评审 |
| [ADR-0003](../decisions/ADR-0003-two-person-ai-workflow.md) | 双人 AI/Git 协作协议 | 双方 | 规范从 Proposed 变为 Accepted |
| [ADR-0004](../decisions/ADR-0004-mysql-data-access.md) | MySQL 数据访问与迁移 | 角色 B，角色 A评审 | 状态：Accepted；生产拓扑和备份策略仍需部署任务确认 |
| [ADR-0005](../decisions/ADR-0005-matching-api-data-contract.md) | 匹配 API 与数据扩展 | 双方 | 状态：Proposed；已授权的任务实现不等于 ADR 已通过评审 |

## 5. 已知阻塞与风险

- 集成分支尚未取得角色 A 的产品/UI 评审结论，不能合入 `main`。
- 真实微信 AppID、微信开发者工具、合法 request 域名和 staging 服务未在当前本机提供，真实微信 code 链路仍需环境验收。
- 全量测试在未设置 `TEAMUP_TEST_MYSQL_URL` 时会跳过真实 MySQL 专属用例；内存与 SQLite 测试不能替代 staging MySQL 验证。
- 轻量模型尚无真实训练数据，必须先通过 P0 事件链积累，不能提前承诺效果。
- 隐私政策、服务条款、内容审核流程尚未形成正式文本。
- 没有真实用户访谈、竞品验证和指标基线，原始数值目标的统计口径待定。

## 6. 下一步建议顺序

1. 角色 B 完成并推送 P0 集成分支，提供可复现的两端验证记录。
2. 角色 A 在 `docs/status/reviews/TUP-20260814-p0-integration-review.md` 核对页面、契约和用户可见行为并写入结论。
3. 双方补做微信开发者工具、合法域名、staging MySQL 和端到端真机验收。
4. 仅在评审文件明确通过后，按 Git 工作流将堆叠任务集成到 `main`。
5. 双方继续评审 ADR-0005、推荐数据保留和轻量模型上线门槛。

## 7. 更新规则

- 新任务：增加一行并链接独立任务文件；
- 合并任务：更新能力状态、移除或标记任务完成，并填写新 `main` SHA；
- 逐步进展：只写任务文件，不持续改本文件；
- 与远程状态不一致时，先以 Git 提交核对，再修正文档，不凭聊天推断。
