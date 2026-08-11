# 架构与产品决策记录（ADR）

> Status: Confirmed<br>
> Owner: 角色 A / 角色 B<br>
> Last Updated: 2026-08-11

ADR 用于保存会跨任务、跨会话影响实现的重要决定。聊天中的同意必须转写为 ADR 才能成为长期项目真值。

## 状态

- `Proposed`：正在讨论，不能作为强制实施结论；
- `Accepted`：双方或指定决策人已确认；
- `Deprecated`：不再建议使用，但保留历史；
- `Superseded`：被新的 ADR 替代，并链接替代项。

## 决策列表

| ADR | Title | Status | Decision Owner |
| --- | --- | --- | --- |
| [ADR-0001](ADR-0001-backend-framework.md) | 后端框架选择 | Accepted | 角色 B，角色 A评审 |
| [ADR-0002](ADR-0002-mvp-ai-scope.md) | 推荐系统与生成式 AI 边界 | Accepted | 角色 A；角色 B实施前评审 |
| [ADR-0003](ADR-0003-two-person-ai-workflow.md) | 双人 AI 与 Git 协作协议 | Proposed | 双方 |
| [ADR-0004](ADR-0004-mysql-data-access.md) | MySQL 数据访问与迁移工具 | Accepted | 角色 B，角色 A评审 |

新增决策时复制 [ADR 模板](ADR-TEMPLATE.md)，编号只增不复用。状态变化保留原始背景、备选方案和影响。
