# TeamUp 文档索引

> Status: Confirmed<br>
> Owner: 角色 A / 角色 B<br>
> Last Updated: 2026-08-14

本目录是 TeamUp 的版本化项目知识库。AI 应根据任务类型读取对应入口，不应无选择地加载所有文件。

## 按任务路由

| 任务类型 | 必读文档 |
| --- | --- |
| 任何行为性修改 | `../AGENTS.md`、`status/CURRENT.md`、对应任务文件 |
| 产品或交互 | `product/PRODUCT_BRIEF.md`、`product/PRD.md`、`product/MVP_SCOPE.md` |
| 后端需求与任务拆分 | `product/BACKEND_PRD.md`、`architecture/API_CONTRACT.md`、`architecture/DATA_MODEL.md` |
| 前后端联调 | `architecture/API_CONTRACT.md`、`architecture/DATA_MODEL.md` |
| 匹配或推荐模型 | `architecture/MATCHING.md`、`architecture/ML_RECOMMENDER.md`、`product/PRD.md`、相关 ADR |
| 架构或依赖 | `architecture/ARCHITECTURE.md`、`decisions/README.md` |
| 开发与 Git | `development/DEVELOPMENT.md`、`development/GIT_WORKFLOW.md` |
| 前后端对接与联调 | `development/FRONTEND_BACKEND_INTEGRATION.md`、`architecture/API_CONTRACT.md`、`architecture/DATA_MODEL.md` |
| 使用 Codex 开发 | `development/AI_WORKFLOW.md`、`status/templates/TASK_TEMPLATE.md` |
| 测试或发布 | `development/TEST_STRATEGY.md`、`development/RELEASE_CHECKLIST.md` |
| 登录、权限、隐私 | `security/SECURITY_AND_PRIVACY.md` |
| 交接或同步 | `status/CURRENT.md`、任务文件、`status/templates/HANDOFF_TEMPLATE.md` |

## 产品

- [产品概要](product/PRODUCT_BRIEF.md)：定位、用户、价值和成功指标。
- [产品需求文档](product/PRD.md)：功能编号、业务规则和验收标准。
- [后端产品需求文档](product/BACKEND_PRD.md)：FastAPI 后端功能、权限、数据、测试和分阶段交付要求。
- [MVP 范围](product/MVP_SCOPE.md)：P0/P1、非目标和发布门槛。
- [用户流程](product/USER_FLOWS.md)：首条 P0 纵向切片及失败、恢复和退出路径。
- [信息架构](product/INFORMATION_ARCHITECTURE.md)：小程序导航、页面层级与权限可见性。
- [页面与状态规范](product/SCREEN_SPEC.md)：页面字段、状态、契约映射和 `GAP-*` 清单。

## 架构

- [系统架构](architecture/ARCHITECTURE.md)：系统边界、模块与技术决策状态。
- [API 契约](architecture/API_CONTRACT.md)：前后端共享接口规则。
- [数据模型](architecture/DATA_MODEL.md)：核心实体、关系与隐私分类。
- [匹配设计](architecture/MATCHING.md)：可解释匹配的候选方案与约束。
- [轻量推荐模型](architecture/ML_RECOMMENDER.md)：数据采集、训练、评估、上线和回退方案。

## 开发

- [开发指南](development/DEVELOPMENT.md)：环境、命令登记和工程约定。
- [Git 工作流](development/GIT_WORKFLOW.md)：双人分支、同步和冲突处理。
- [前后端对接与联调指南](development/FRONTEND_BACKEND_INTEGRATION.md)：契约、mock、环境、联调、验收和 Fork 交付流程。
- [AI 协作流程](development/AI_WORKFLOW.md)：Codex 任务协议和防越界规则。
- [测试策略](development/TEST_STRATEGY.md)：测试层级和质量门槛。
- [发布清单](development/RELEASE_CHECKLIST.md)：发布前、发布中和回滚检查。

## 安全

- [安全与隐私](security/SECURITY_AND_PRIVACY.md)：学生数据、鉴权、日志和 AI 安全要求。

## 决策与状态

- [ADR 索引](decisions/README.md)：已接受和待确认的关键决策。
- [当前状态](status/CURRENT.md)：`main` 分支唯一聚合状态。
- [任务目录](status/tasks/README.md)：各分支独立任务状态。
- [角色 B 文档与技术基线评审](status/reviews/TUP-20260810-role-b-review.md)：无需 PR 的核对范围、Codex 提示词和结论模板。
- [前后端对接指南角色 A 评审](status/reviews/TUP-20260810-role-a-frontend-integration-review.md)：角色 A 对页面、mock 和联调流程的核对范围与结论模板。
- [角色 A 产品基础技术评审](status/reviews/TUP-20260810-role-a-product-foundation-review.md)：登录、名片与项目发布切片的 `GAP-*` 核对模板。
- [FastAPI 后端决策角色 A 评审](status/reviews/TUP-20260811-fastapi-backend-review.md)：角色 A 对契约和用户可见影响的评审入口。
- [前端 foundation 角色 B 评审](status/reviews/TUP-20260811-frontend-foundation-review.md)：角色 B 对前端契约、安全边界和构建结果的评审记录。
- [MySQL 持久化角色 A 评审](status/reviews/TUP-20260811-mysql-persistence-review.md)：角色 A 对持久化切换、契约兼容和前端影响的评审入口。
- [match-v0.1 角色 A 评审](status/reviews/TUP-20260811-match-v0-1-review.md)：角色 A 对规则权重、解释代码和后续字段契约的评审入口。
- [匹配 API/数据契约角色 A 评审](status/reviews/TUP-20260811-match-api-data-contract-review.md)：角色 A 对岗位粒度、匹配偏好、分页、曝光和兼容迁移的决策入口。
- [匹配偏好与岗位约束角色 A 评审](status/reviews/TUP-20260812-match-preferences-review.md)：角色 A 对首批匹配输入实现、旧前端兼容和迁移默认值的验收入口。
- [项目成员与岗位容量角色 A 评审](status/reviews/TUP-20260812-project-members-review.md)：角色 A 对容量展示、成员列表权限和邀请前置边界的验收入口。
- [用户拉黑与安全过滤角色 A 评审](status/reviews/TUP-20260812-user-blocks-review.md)：角色 A 对拉黑幂等、隐私反馈和跨模块阻断边界的验收入口。
- [项目岗位邀请角色 A 评审](status/reviews/TUP-20260812-project-invitations-review.md)：角色 A 对邀请有效期、状态机、权限、容量和拉黑边界的验收入口。
- [双人会话与文本消息角色 A 评审](status/reviews/TUP-20260812-conversations-messages-review.md)：角色 A 对会话上下文、消息幂等、分页、权限和拉黑边界的验收入口。
- [前端真实 API adapter 角色 A 评审](status/reviews/TUP-20260814-frontend-api-adapter-review.md)：角色 A 对微信登录、真实 API 模式和前端错误状态的评审入口。
- [项目 PUT 兼容角色 A 评审](status/reviews/TUP-20260814-project-put-compat-review.md)：角色 A 对微信请求方法兼容与项目更新语义的评审入口。
- [P0 前后端集成角色 A 评审](status/reviews/TUP-20260814-p0-integration-review.md)：组合分支的测试、构建、联调与剩余环境风险评审入口。
- [任务模板](status/templates/TASK_TEMPLATE.md)、[交接模板](status/templates/HANDOFF_TEMPLATE.md) 和 [模型发布模板](status/templates/MODEL_RELEASE_TEMPLATE.md)。

## 历史来源

仓库根目录两份 PDF 是初始产品与团队共识材料。若 PDF 与已接受 ADR 或当前规范冲突，以已接受 ADR 和当前版本化规范为准，同时记录冲突来源。
