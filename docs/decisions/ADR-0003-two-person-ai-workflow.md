# ADR-0003: 双人 AI 与 Git 协作协议

> Status: Proposed<br>
> Decision Owners: 角色 A / 角色 B<br>
> Date: 2026-08-10

## Context

两位成员会分别使用 Codex 开发。如果只靠聊天同步，容易发生同文件覆盖、接口漂移、重复任务、AI 越权修改、测试结果不可追溯和交接后无法恢复。

## Decision

建议接受以下协议：

- 根 `AGENTS.md` 作为所有 Codex 任务的强制入口；
- `main` 只接收评审后的集成结果；
- 一任务一负责人、一分支、一任务状态文件；
- 公共契约指定唯一编辑者并先于并行实现；
- `CURRENT.md` 只维护主分支聚合状态，不写实时日志；
- 重要决定写 ADR，跨角色继续工作写交接记录；
- QQ 只用于通知，决定、状态、交接和评审结论必须写回仓库；
- AI 默认不能 commit、push、merge 或部署；
- 代码、测试、文档与状态在同一任务分支和评审批次同步；
- Pull Request 可选；另一角色在仓库评审文件中留下明确结论后才能集成到 `main`。

完整规则见 [Git 工作流](../development/GIT_WORKFLOW.md) 和 [AI 协作流程](../development/AI_WORKFLOW.md)。

## Alternatives

### 共用长期开发分支

文件少时简单，但两个 AI 并发工作会频繁覆盖和混合责任，不采用。

### 只用 GitHub Issue/聊天记录

依赖外部状态和人工保持一致，新 Codex 会话可能无法获得完整上下文，不作为唯一真值。

### 每次都修改一个共享状态日志

可见性高但冲突频繁。采用“任务文件分片 + CURRENT 聚合”替代。

## Consequences

- 每个任务增加少量文档成本；
- 并行边界、评审责任和恢复路径更清晰；
- 双方需在集成时把任务状态和评审结论汇总到 `CURRENT.md`；
- 接受本 ADR 后，将相关工作流文档状态改为 `Confirmed`。
