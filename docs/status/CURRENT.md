# TeamUp 当前状态

> Status: Confirmed<br>
> Snapshot Branch: `main`<br>
> Remote Baseline: `167edd5`<br>
> Last Updated: 2026-08-10 by 角色 A

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
| 后端工程 | Blocked by decision | 等待 FastAPI / Spring Boot 决策 |
| 部署环境 | Not started | 腾讯云方向已知，具体拓扑未确定 |

## 3. 活跃任务

| Task ID | Owner | Area | Status | Working location | Record |
| --- | --- | --- | --- | --- | --- |
| TUP-20260810-docs-baseline | 角色 A | 文档、AI 协作与推荐策略基线 | Ready for Review | `role-a/docs/TUP-20260810-docs-baseline` | [任务记录](tasks/TUP-20260810-docs-baseline.md) |

角色 B 当前没有登记中的任务。开始开发前必须新建独立任务文件和分支。

## 4. 关键决策

| ADR | 事项 | Owner | 阻塞内容 |
| --- | --- | --- | --- |
| [ADR-0001](../decisions/ADR-0001-backend-framework.md) | FastAPI 或 Spring Boot | 角色 B，角色 A评审 | 后端工程初始化和真实开发命令 |
| [ADR-0002](../decisions/ADR-0002-mvp-ai-scope.md) | 规则算法 P0 + 自训练轻量模型 P1 | 角色 A已确认，角色 B实施前评审 | 状态：Accepted；模型启用门槛待数据评审 |
| [ADR-0003](../decisions/ADR-0003-two-person-ai-workflow.md) | 双人 AI/Git 协作协议 | 双方 | 规范从 Proposed 变为 Accepted |

## 5. 已知阻塞与风险

- 后端框架未定，不能生成真实后端项目、命令和 CI。
- 轻量模型尚无真实训练数据，必须先通过 P0 事件链积累，不能提前承诺效果。
- 隐私政策、服务条款、内容审核流程尚未形成正式文本。
- 没有真实用户访谈、竞品验证和指标基线，原始数值目标的统计口径待定。

## 6. 下一步建议顺序

1. 角色 A、B 评审并接受/修改 ADR-0003，先统一协作规则。
2. 角色 B 主导确认 ADR-0001，初始化后端工程和真实命令。
3. 双方按 ADR-0002 评审推荐事件、特征 schema 和模型上线门槛。
4. 双方按 API 契约确定首条纵向切片：登录 -> 名片 -> 项目发布。
5. 建立 CI、测试数据库和 staging 后再并行扩展匹配与沟通。

## 7. 更新规则

- 新任务：增加一行并链接独立任务文件；
- 合并任务：更新能力状态、移除或标记任务完成，并填写新 `main` SHA；
- 逐步进展：只写任务文件，不持续改本文件；
- 与远程状态不一致时，先以 Git 提交核对，再修正文档，不凭聊天推断。
