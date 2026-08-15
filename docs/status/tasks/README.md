# 任务状态目录

> Status: Confirmed<br>
> Owner: 角色 A / 角色 B<br>
> Last Updated: 2026-08-16

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
- [TUP-20260810-role-a-product-foundation](TUP-20260810-role-a-product-foundation.md)
- [TUP-20260810-backend-frontend-integration](TUP-20260810-backend-frontend-integration.md)
- [TUP-20260811-fastapi-backend](TUP-20260811-fastapi-backend.md)
- [TUP-20260811-frontend-foundation](TUP-20260811-frontend-foundation.md)
- [TUP-20260811-wechat-login](TUP-20260811-wechat-login.md)
- [TUP-20260811-mysql-persistence](TUP-20260811-mysql-persistence.md)
- [TUP-20260811-match-v0-1](TUP-20260811-match-v0-1.md)
- [TUP-20260811-match-api-data-contract](TUP-20260811-match-api-data-contract.md)
- [TUP-20260812-match-preferences](TUP-20260812-match-preferences.md)
- [TUP-20260812-project-members](TUP-20260812-project-members.md)
- [TUP-20260812-user-blocks](TUP-20260812-user-blocks.md)
- [TUP-20260812-project-invitations](TUP-20260812-project-invitations.md)
- [TUP-20260812-conversations-messages](TUP-20260812-conversations-messages.md)
- [TUP-20260813-account-deletion-requests](TUP-20260813-account-deletion-requests.md)
- [TUP-20260813-audit-events](TUP-20260813-audit-events.md)
- [TUP-20260813-ci-contract-gate](TUP-20260813-ci-contract-gate.md)
- [TUP-20260813-discovery](TUP-20260813-discovery.md)
- [TUP-20260813-error-boundary](TUP-20260813-error-boundary.md)
- [TUP-20260813-logout-audit](TUP-20260813-logout-audit.md)
- [TUP-20260813-matching-api](TUP-20260813-matching-api.md)
- [TUP-20260813-rate-limit-cleanup](TUP-20260813-rate-limit-cleanup.md)
- [TUP-20260813-rate-limiting](TUP-20260813-rate-limiting.md)
- [TUP-20260813-readiness-boundary](TUP-20260813-readiness-boundary.md)
- [TUP-20260813-recommendation-impressions](TUP-20260813-recommendation-impressions.md)
- [TUP-20260813-reports](TUP-20260813-reports.md)
- [TUP-20260813-request-observability](TUP-20260813-request-observability.md)
- [TUP-20260814-frontend-api-adapter](TUP-20260814-frontend-api-adapter.md)
- [TUP-20260814-project-put-compat](TUP-20260814-project-put-compat.md)
- [TUP-20260814-p0-integration](TUP-20260814-p0-integration.md)
- [TUP-20260815-ui-refinement](TUP-20260815-ui-refinement.md)
- [TUP-20260815-cloudbase-transport](TUP-20260815-cloudbase-transport.md)

跨角色评审：

- [TUP-20260810-role-b-review](../reviews/TUP-20260810-role-b-review.md)
- [TUP-20260810-role-a-frontend-integration-review](../reviews/TUP-20260810-role-a-frontend-integration-review.md)
- [TUP-20260810-role-a-product-foundation-review](../reviews/TUP-20260810-role-a-product-foundation-review.md)
- [TUP-20260811-fastapi-backend-review](../reviews/TUP-20260811-fastapi-backend-review.md)
- [TUP-20260811-frontend-foundation-review](../reviews/TUP-20260811-frontend-foundation-review.md)
- [TUP-20260811-wechat-login-review](../reviews/TUP-20260811-wechat-login-review.md)
- [TUP-20260811-mysql-persistence-review](../reviews/TUP-20260811-mysql-persistence-review.md)
- [TUP-20260811-match-v0-1-review](../reviews/TUP-20260811-match-v0-1-review.md)
- [TUP-20260811-match-api-data-contract-review](../reviews/TUP-20260811-match-api-data-contract-review.md)
- [TUP-20260812-match-preferences-review](../reviews/TUP-20260812-match-preferences-review.md)
- [TUP-20260812-project-members-review](../reviews/TUP-20260812-project-members-review.md)
- [TUP-20260812-user-blocks-review](../reviews/TUP-20260812-user-blocks-review.md)
- [TUP-20260812-project-invitations-review](../reviews/TUP-20260812-project-invitations-review.md)
- [TUP-20260812-conversations-messages-review](../reviews/TUP-20260812-conversations-messages-review.md)
- [TUP-20260813-account-deletion-requests-review](../reviews/TUP-20260813-account-deletion-requests-review.md)
- [TUP-20260813-audit-events-review](../reviews/TUP-20260813-audit-events-review.md)
- [TUP-20260813-ci-contract-gate-review](../reviews/TUP-20260813-ci-contract-gate-review.md)
- [TUP-20260813-discovery-review](../reviews/TUP-20260813-discovery-review.md)
- [TUP-20260813-error-boundary-review](../reviews/TUP-20260813-error-boundary-review.md)
- [TUP-20260813-logout-audit-review](../reviews/TUP-20260813-logout-audit-review.md)
- [TUP-20260813-matching-api-review](../reviews/TUP-20260813-matching-api-review.md)
- [TUP-20260813-rate-limit-cleanup-review](../reviews/TUP-20260813-rate-limit-cleanup-review.md)
- [TUP-20260813-rate-limiting-review](../reviews/TUP-20260813-rate-limiting-review.md)
- [TUP-20260813-readiness-boundary-review](../reviews/TUP-20260813-readiness-boundary-review.md)
- [TUP-20260813-recommendation-impressions-review](../reviews/TUP-20260813-recommendation-impressions-review.md)
- [TUP-20260813-reports-review](../reviews/TUP-20260813-reports-review.md)
- [TUP-20260813-request-observability-review](../reviews/TUP-20260813-request-observability-review.md)
- [TUP-20260814-frontend-api-adapter-review](../reviews/TUP-20260814-frontend-api-adapter-review.md)
- [TUP-20260814-project-put-compat-review](../reviews/TUP-20260814-project-put-compat-review.md)
- [TUP-20260814-p0-integration-review](../reviews/TUP-20260814-p0-integration-review.md)
- [TUP-20260815-ui-refinement-review](../reviews/TUP-20260815-ui-refinement-review.md)
- [TUP-20260815-cloudbase-transport-review](../reviews/TUP-20260815-cloudbase-transport-review.md)
