# TUP-20260811-match-api-data-contract: 匹配 API 与数据契约设计

> Status: Ready for Review<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `941494b`<br>
> Branch: `role-b/docs/TUP-20260811-match-api-data-contract`<br>
> Last Updated: 2026-08-11

## 1. 目标

在不发布代码和迁移的前提下，补齐 `match-v0.1` 接入双向匹配 API 所需的请求、响应、分页、隐私和数据契约，交由角色 A 评审。

## 2. 依据

- 产品：`MATCH-001/002/003`、`FLOW-01/02`
- 后端：`BE-MATCH-001/002/003`、`BE-E2E-005`
- API：`API-MATCH-01/02/03`
- 算法：[MATCHING.md](../../architecture/MATCHING.md)
- 决策：[ADR-0002](../../decisions/ADR-0002-mvp-ai-scope.md)

## 3. 范围

- 双向岗位级匹配的查询参数、响应 DTO、分页和错误语义；
- `recommendationRequestId`、候选快照和曝光去重；
- required skill、方向偏好、时间段、经历、成员容量和拉黑所需数据；
- 兼容现有名片、项目和岗位字段的迁移策略；
- 安全、隐私和角色 A 评审清单。

## 4. 非目标

- 不实现路由、ORM、迁移或前端页面；
- 不实现 P1 模型、消息、邀请或举报流程；
- 不把 Proposed 字段表述为已确认接口；
- 不决定尚无数据证据的模型启用门槛。

## 5. 计划

- [x] 创建独立设计分支和任务记录；
- [x] 提出 API-MATCH-01/02/03 完整契约；
- [x] 提出数据实体、约束、索引和兼容迁移；
- [x] 记录备选方案和推荐决策；
- [x] 建立角色 A 评审入口；
- [x] 检查文档链接和契约一致性。

## 6. 验收标准

- [x] 前端可以据文档确定请求、分页、展示目标和错误处理；
- [x] 两个方向都明确到岗位粒度且使用兼容 MatchResult；
- [x] 翻页结果稳定，曝光只能引用服务端签发候选；
- [x] 历史 `skills` 不被静默当作 required；
- [x] 拉黑、关闭、容量和隐私在服务端过滤边界中明确；
- [x] 需要角色 A 确认的事项全部标为 Proposed/TBD。

## 7. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git fetch --prune origin` via `127.0.0.1:7897` | Passed | 基线 `941494b` 已在远程匹配引擎分支 |
| Changed-document relative link check | Passed | 新增 ADR、任务、评审及交叉链接均存在 |
| `python -m pytest -ra` | Passed | 41 passed，2 skipped；跳过项需要 `TEAMUP_TEST_MYSQL_URL` |
| `git diff --check` | Passed | 无空白错误 |
| API/data consistency review | Passed | 岗位粒度、required subset、快照分页、实时再鉴权和曝光唯一键一致 |

## 8. 当前状态与下一步

- 当前：设计已完成，等待角色 A 按评审文件确认 MA-001..013。
- 下一步：角色 A 评审；Accepted 后另建功能分支实现 schema、候选查询、端点和曝光。
- 最后相关提交：本任务提交 `docs(matching): propose API and data contract`
