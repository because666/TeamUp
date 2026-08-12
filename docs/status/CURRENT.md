# TeamUp 当前状态

> Status: Confirmed<br>
> Snapshot Branch: `main`<br>
> Remote Baseline: `167edd5`<br>
> Last Updated: 2026-08-12 by 角色 B

本文件只记录已合并或正在明确交接的聚合状态，不记录逐步开发日志。单个任务的实时进展见 `tasks/`。

## 1. 项目阶段

当前处于“文档与工程基线建设”阶段。远程仓库只有初始 README，业务工程尚未初始化。

## 2. 当前能力

| 范围 | 状态 | 说明 |
| --- | --- | --- |
| 原始需求 | Available | 两份 PDF 已保留在仓库根目录 |
| 产品规范 | Ready for review | 已转为带需求 ID、验收标准和范围边界的 Markdown |
| AI 协作治理 | Ready for review | 根 AGENTS、双人工作流、任务/交接模板已建立 |
| 技术架构 | Proposed | 模块化单体和契约基线待双方评审 |
| 前端工程 | Not started | UniApp 方向已知，版本与命令未确定 |
| 后端工程 | Ready for spike | FastAPI 已确认，等待纵向验证和工程初始化 |
| 部署环境 | Not started | 腾讯云方向已知，具体拓扑未确定 |

## 3. 活跃任务

| Task ID | Owner | Area | Status | Working location | Record |
| --- | --- | --- | --- | --- | --- |
| TUP-20260810-docs-baseline | 角色 A | 文档、AI 协作与推荐策略基线 | Ready for Review | `role-a/docs/TUP-20260810-docs-baseline` | [任务记录](tasks/TUP-20260810-docs-baseline.md) |
| TUP-20260810-role-b-review | 角色 B | 文档、后端可行性、安全与协作规则核对 | Pending | `origin/role-a/docs/TUP-20260810-docs-baseline` | [评审记录](reviews/TUP-20260810-role-b-review.md) |
| TUP-20260810-role-a-product-foundation | 角色 A | 用户流程、信息架构与页面状态规范 | Ready to Start | `role-a/docs/TUP-20260810-role-a-product-foundation` | [任务记录](tasks/TUP-20260810-role-a-product-foundation.md) |
| TUP-20260810-backend-frontend-integration | 角色 B | 前后端契约、mock、联调与交付流程 | Proposed | `role-a/docs/TUP-20260810-role-a-product-backend` | [任务记录](tasks/TUP-20260810-backend-frontend-integration.md) |
| TUP-20260811-fastapi-backend | 角色 B | FastAPI 框架决策、完整后端 PRD 与初始化准备 | Proposed | `role-b/docs/TUP-20260811-fastapi-backend` | [任务记录](tasks/TUP-20260811-fastapi-backend.md) |
| TUP-20260811-match-v0-1 | 角色 B | 可解释规则匹配引擎与 golden tests | Ready for Review | `role-b/feature/TUP-20260811-match-v0-1` | [任务记录](tasks/TUP-20260811-match-v0-1.md) |
| TUP-20260811-match-api-data-contract | 角色 B | 匹配 API、分页与数据扩展契约 | Ready for Review | `role-b/docs/TUP-20260811-match-api-data-contract` | [任务记录](tasks/TUP-20260811-match-api-data-contract.md) |
| TUP-20260812-match-preferences | 角色 B | 匹配偏好与岗位匹配字段 | Ready for Review | `role-b/feature/TUP-20260812-match-preferences` | [任务记录](tasks/TUP-20260812-match-preferences.md) |
| TUP-20260812-project-members | 角色 B | 项目成员与岗位容量 | Ready for Review | `role-b/feature/TUP-20260812-project-members` | [任务记录](tasks/TUP-20260812-project-members.md) |
| TUP-20260812-user-blocks | 角色 B | 用户拉黑与安全过滤 | Ready for Review | `role-b/feature/TUP-20260812-user-blocks` | [任务记录](tasks/TUP-20260812-user-blocks.md) |

角色 A 的产品基础任务可以与角色 B 的技术基线评审并行；双方不得修改对方的任务文件或高冲突契约。

## 4. 关键决策

| ADR | 事项 | Owner | 阻塞内容 |
| --- | --- | --- | --- |
| [ADR-0001](../decisions/ADR-0001-backend-framework.md) | FastAPI | 角色 B已确认，角色 A评审 | 状态：Accepted；具体版本和工具链待初始化验证 |
| [ADR-0002](../decisions/ADR-0002-mvp-ai-scope.md) | 规则算法 P0 + 自训练轻量模型 P1 | 角色 A已确认，角色 B实施前评审 | 状态：Accepted；模型启用门槛待数据评审 |
| [ADR-0003](../decisions/ADR-0003-two-person-ai-workflow.md) | 双人 AI/Git 协作协议 | 双方 | 规范从 Proposed 变为 Accepted |

## 5. 已知阻塞与风险

- FastAPI 已确定，但运行时、依赖、数据访问、迁移和测试工具尚未通过纵向验证，暂不能把具体命令标记为可用。
- 轻量模型尚无真实训练数据，必须先通过 P0 事件链积累，不能提前承诺效果。
- 隐私政策、服务条款、内容审核流程尚未形成正式文本。
- 没有真实用户访谈、竞品验证和指标基线，原始数值目标的统计口径待定。

## 6. 下一步建议顺序

1. 角色 A 通过 QQ 通知角色 B 按评审文件核对；结论必须回写仓库，PR 可选。
2. 角色 A 启动产品基础任务，先完成登录 -> 名片 -> 项目发布的流程、页面和契约映射，不锁定工程工具链。
3. 角色 B 按 ADR-0001 完成 FastAPI 纵向验证，再初始化后端工程和真实命令。
4. 双方按 ADR-0002 评审推荐事件、特征 schema 和模型上线门槛。
5. 契约评审通过后再建立 CI、测试数据库和 staging，并行扩展匹配与沟通。

## 7. 更新规则

- 新任务：增加一行并链接独立任务文件；
- 合并任务：更新能力状态、移除或标记任务完成，并填写新 `main` SHA；
- 逐步进展：只写任务文件，不持续改本文件；
- 与远程状态不一致时，先以 Git 提交核对，再修正文档，不凭聊天推断。
