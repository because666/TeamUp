# TUP-20260812-user-blocks: 用户拉黑与安全过滤

> Status: Ready for Review<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `3cb85a2`<br>
> Branch: `role-b/feature/TUP-20260812-user-blocks`<br>
> Last Updated: 2026-08-12

## 1. 目标

提供用户拉黑/取消拉黑能力，并让后续成员、消息、邀请和匹配查询可以统一执行双向安全阻断。

## 2. 依据

- PRD：`SAFE-001`、`BE-SAFE-001/002/003`、`BE-SEC-008`、`BE-E2E-008`；
- API：`API-SAFE-02`、`API-SAFE-03`；
- ADR：N/A；用户于 2026-08-12 明确要求按推荐顺序继续后端模块。

## 3. 范围

- `blocks` ORM、MySQL/Alembic 迁移和 memory/SQL repository；
- `POST /api/v1/blocks`、`DELETE /api/v1/blocks/{blockedUserId}`；
- 自己拉黑、目标存在性、重复请求和取消幂等；
- 双向 `is_blocked_between` 查询；
- 成员创建内部事务接入双向拉黑阻断；
- API、权限、唯一约束、并发和隐私测试；
- API、数据、迁移、任务与角色 A 评审文档同步。

## 4. 非目标

- 不实现举报、管理员处理、审计后台或注销；
- 不实现消息/邀请/匹配列表，只接入已有成员原子入队的安全检查；
- 不返回拉黑原因、时间线或对方是否拉黑当前用户；
- 不自动删除既有成员、邀请、会话或历史数据；
- 不合入 `main`，直到角色 A 评审。

## 5. 依赖与假设

- 本分支堆叠在已推送的成员分支 `3cb85a2` 上；
- 一个用户只能创建自己发起的 `(blocker_id, blocked_id)` 关系，组合唯一；
- `POST` 重复拉黑返回已存在关系，`DELETE` 不存在关系返回 `removed=false`；
- 被拉黑关系不向任一用户公开细节；查询只返回布尔结果给服务端内部调用；
- 拉黑不影响既有项目成员关系，后续新消息、新邀请和匹配候选必须查询双向阻断。

## 6. 计划

- [x] 建立独立任务并记录隐私、幂等和非目标边界；
- [x] 扩展 DTO、repository 协议和 memory 实现；
- [x] 实现 SQL 唯一约束、双向查询和内部成员阻断；
- [x] 创建第四版 Alembic 迁移；
- [x] 接入拉黑/取消拉黑 FastAPI 路由；
- [x] 增加未认证、自拉黑、IDOR、重复/并发和阻断测试；
- [x] 同步文档并建立角色 A 评审入口。

## 7. 验收标准

- [x] 认证用户可拉黑有效目标，自己拉黑和不存在目标被稳定拒绝；
- [x] 重复拉黑和重复取消均幂等，不泄露关系细节；
- [x] 任一方向存在关系时，内部 `users_blocked` 返回 true；
- [x] 成员原子入队遇到双向拉黑返回 `USER_BLOCKED`，不写入成员；
- [x] MySQL 唯一约束、迁移回滚和重复请求通过；
- [x] API、数据、安全文档和评审文件同步。

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-12 | 创建堆叠任务分支 | 匹配、消息和邀请都依赖统一拉黑过滤 |
| 2026-08-12 | 只提供布尔内部查询 | 不向客户端暴露拉黑关系细节 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git fetch --prune origin` via `127.0.0.1:7897` | Passed | 前置提交 `3cb85a2` 已推送 |
| `python -m pytest -ra` with disposable MySQL 8.4 | Passed | 55 tests；包含真实 MySQL 拉黑持久化、成员阻断和完整回归 |
| `python -m alembic check` against MySQL 8.4 | Passed | ORM 与 `20260812_0004` 无 schema 漂移 |
| `upgrade head -> downgrade base -> upgrade head` against MySQL 8.4 | Passed | 第四版迁移、约束、回滚和重建通过；一次性容器已删除 |
| `python -m pytest -ra` without MySQL URL | Passed | 51 passed，4 个 MySQL 专属测试按配置跳过 |
| `python -m compileall -q app tests` | Passed | 应用与测试模块编译通过 |
| `git diff --check` | Passed | 无空白错误 |

## 10. 当前状态与下一步

- 最后完成：拉黑/取消、双向阻断、成员接入、迁移、文档与真实 MySQL 验证。
- 当前阻塞：无实现阻塞；等待角色 A 按堆叠顺序评审。
- 下一步：后续消息、邀请、发现和匹配模块复用 `users_blocked`，不能自行复制关系语义。
- 剩余风险：未实现举报、拉黑列表、消息/邀请/匹配过滤、限流和审计事件。
- 最后相关提交：`feat(safety): add user blocks and enforcement`
