# TeamUp

TeamUp 是面向高校学生竞赛、科研与创业项目的智能组队平台。产品目标是通过结构化能力名片、项目招募信息和可解释匹配，跑通“发布项目 -> 匹配队友 -> 沟通组队”的完整闭环。

## 当前阶段

仓库处于文档与工程基线建设阶段，尚未提交业务代码。

- 已确认：微信小程序方向、UniApp 前端、MySQL、腾讯云部署方向、双人核心团队。
- 已确认：推荐系统先采用可解释规则算法，积累真实数据后训练平台自己的轻量机器学习排序模型；通用大模型不参与最终匹配分数。
- 待决策：后端采用 FastAPI 还是 Spring Boot、轻量排序模型的启用数据门槛、搜索与向量数据库何时引入。
- 当前工作状态以 [CURRENT.md](docs/status/CURRENT.md) 为准。
- 已确认和待确认的技术决策以 [决策目录](docs/decisions/README.md) 为准。

## 团队分工

| 角色 | 主要责任 |
| --- | --- |
| 角色 A | 产品、前端、AI 模块、运营与赛事材料 |
| 角色 B | 后端、架构、数据库、部署、运维与安全 |

职责边界不代表禁止协作。跨边界修改必须先写清接口、影响范围和负责人，具体规则见 [协作与 Git 工作流](docs/development/GIT_WORKFLOW.md)。

## 文档入口

- [AGENTS.md](AGENTS.md)：Codex 必须遵守的仓库级规则
- [文档总索引](docs/README.md)：产品、架构、开发、测试、安全与状态文档
- [产品需求](docs/product/PRD.md)：带需求编号和验收标准的 MVP 需求
- [MVP 范围](docs/product/MVP_SCOPE.md)：首版边界、非目标和发布门槛
- [系统架构](docs/architecture/ARCHITECTURE.md)：当前架构约束与待决策项
- [AI 协作流程](docs/development/AI_WORKFLOW.md)：两人使用 Codex 的任务协议
- [当前状态](docs/status/CURRENT.md)：唯一的主分支状态快照
- [任务模板](docs/status/templates/TASK_TEMPLATE.md)：每个开发分支的状态记录模板

## 开始工作

1. 从仓库根目录启动 Codex，使其自动读取 [AGENTS.md](AGENTS.md)。
2. 阅读 [CURRENT.md](docs/status/CURRENT.md) 和相关任务文件。
3. 同步远程分支并确认工作区状态。
4. 使用任务分支开发，不直接在 `main` 上并行修改。
5. 代码、测试、接口文档和任务状态在同一个 PR 中同步提交。

工程初始化完成后，必须在 [DEVELOPMENT.md](docs/development/DEVELOPMENT.md) 中补充可直接执行的安装、启动、测试和构建命令。在此之前，AI 不得猜测命令或虚构已存在的项目结构。

## 原始资料

- [TeamUp 大学生竞赛组队平台产品需求文档（MVP 版）](TeamUp大学生竞赛组队平台_产品需求文档（MVP版）.pdf)
- [大学生创新项目智能匹配平台：项目共识与团队分工说明书](大学生创新项目智能匹配平台.pdf)

原始 PDF 用于追溯项目初始共识；后续实施以仓库内已确认的版本化 Markdown 文档和 ADR 为准。
