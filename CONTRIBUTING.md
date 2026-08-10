# TeamUp 贡献指南

本仓库由两位核心成员配合 Codex 开发。任何贡献都必须同时维护实现、验证证据和共享状态，避免“代码已变、另一方不知道”的情况。

## 开始前

1. 阅读根目录 [AGENTS.md](AGENTS.md)。
2. 阅读 [当前状态](docs/status/CURRENT.md) 和相关决策。
3. 从最新 `origin/main` 创建个人任务分支。
4. 使用 [任务模板](docs/status/templates/TASK_TEMPLATE.md) 建立任务文件。

## 分支和提交

- 角色 A：`role-a/<type>/<task-id>-<slug>`
- 角色 B：`role-b/<type>/<task-id>-<slug>`
- 类型使用 `feature`、`fix`、`docs`、`refactor` 或 `chore`。
- 示例：`role-a/feature/TUP-012-project-publish-form`。
- 提交信息格式：`<type>(<scope>): <summary>`。
- 示例：`feat(project): add draft validation`。

一个提交应表达一个可解释的变化。不要把无关格式化、依赖升级和功能修改混在一起。

## 评审与集成

另一角色评审是集成到 `main` 的必要条件，Pull Request 是可选载体。评审结论必须写入 `docs/status/reviews/` 下的独立文件；如果使用 PR，PR 描述也应引用该评审文件。

评审记录必须填写：

- 关联任务和负责人；
- 变更范围及明确的非目标；
- API、数据、产品和安全影响；
- 实际运行的验证命令与结果；
- 截图或接口样例（适用时）；
- 文档和状态同步情况；
- 风险、回滚方式和待处理事项。

QQ 只发送查看分支、请求评审和评审完成通知，不能代替仓库中的任务、评审、ADR 或交接记录。

涉及另一角色职责范围的改动，必须由对应角色评审。公共接口或数据结构改变时，契约文档应先于或与实现同时合并。

## 合并要求

- 分支已基于最新 `origin/main` 检查冲突；
- 必需检查通过；
- 验收标准有证据；
- 文档与状态同步；
- 至少一位另一角色完成评审；
- 不包含密钥、个人数据、调试文件和无关改动。

详细流程见 [Git 工作流](docs/development/GIT_WORKFLOW.md) 和 [AI 协作流程](docs/development/AI_WORKFLOW.md)。
