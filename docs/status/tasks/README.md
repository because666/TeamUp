# 任务状态目录

> Status: Confirmed<br>
> Owner: 角色 A / 角色 B<br>
> Last Updated: 2026-08-10

每个会改变产品行为、API、数据、依赖、部署或团队规范的任务都使用独立 Markdown 文件。文件名使用 `<TASK-ID>.md`，从 [任务模板](../templates/TASK_TEMPLATE.md) 创建。

规则：

- 一个任务文件只有一个负责人和一个主工作分支；
- 负责人在任务开始、重要范围变化、验证完成和交接时更新；
- 不记录完整聊天或逐分钟日志，只记录可恢复工作的事实；
- 完成后保留文件作为历史，不移动或重命名导致链接失效；
- 被替代的任务标记 `Superseded` 并链接新任务；
- 两个分支不得同时修改同一个任务文件。

当前任务：

- [TUP-20260810-docs-baseline](TUP-20260810-docs-baseline.md)
