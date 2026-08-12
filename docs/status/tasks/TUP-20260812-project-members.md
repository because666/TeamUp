# TUP-20260812-project-members: 项目成员与岗位容量

> Status: Ready for Review<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `2edb4b1`<br>
> Branch: `role-b/feature/TUP-20260812-project-members`<br>
> Last Updated: 2026-08-12

## 1. 目标

建立可持久化、并发安全的项目成员与岗位容量基础，使后续邀请接受事务能原子创建唯一成员且不能让岗位超额。

## 2. 依据

- PRD：`BE-GOAL-003`、`BE-PROJ-002/003`、`BE-TEAM-002`、`BE-E2E-007`；
- API：新增 `API-PROJ-MEMBER-01`，并扩展现有岗位响应的容量字段；
- ADR：N/A；用户于 2026-08-12 明确要求按推荐顺序继续后端模块。

## 3. 范围

- `project_members` ORM、MySQL/Alembic 迁移和 memory/SQL repository；
- 岗位 `filledCount`、`remainingCount` 动态容量；
- `GET /api/v1/projects/{projectId}/members`；
- 仅项目 owner 或有效成员读取成员列表；
- 供后续邀请接受事务调用的原子成员创建方法；
- 唯一成员、岗位开放/项目发布、容量和并发测试；
- API、数据、迁移、任务与角色 A 评审文档同步。

## 4. 非目标

- 不开放“用户自行加入”或“owner 直接添加成员”的 HTTP 接口；
- 不实现邀请创建、接受、拒绝和幂等键；
- 不实现成员退出、踢出、换岗或 owner 转移；
- 不实现拉黑、会话、匹配列表或推荐快照；
- 不合入 `main`，直到角色 A 评审前置分支与本分支。

## 5. 依赖与假设

- 本分支堆叠在已推送的 `role-b/feature/TUP-20260812-match-preferences`（`2edb4b1`）上；
- 成员只能由后续已授权业务事务创建，本任务不提供绕过邀请流程的公共写接口；
- 一个用户在同一项目最多有一条有效成员关系；P0 不支持同时占多个岗位；
- `headcount` 是岗位容量，`ACTIVE` 成员计入容量；成员退出状态及状态转换保持后续任务 `TBD`；
- 读取成员列表返回内部 opaque `userId`、岗位和加入时间，不返回微信身份、联系方式或完整名片。

## 6. 计划

- [x] 建立独立任务并记录接口、权限和非目标；
- [x] 扩展 DTO、repository 协议和 memory 实现；
- [x] 实现 SQL 行锁、容量检查和成员查询；
- [x] 创建第三版 Alembic 迁移；
- [x] 接入成员读取路由和 OpenAPI；
- [x] 增加权限、状态、唯一性、容量及并发测试；
- [x] 同步文档并建立角色 A 评审入口。

## 7. 验收标准

- [x] 项目发布且岗位开放、有剩余容量时可由内部事务创建唯一成员；
- [x] 草稿/关闭项目、关闭/不存在岗位、重复成员和满员均返回稳定错误；
- [x] 并发竞争最后一个名额时最多一个成功；
- [x] owner 和有效成员可读取列表，其他用户收到 `403`，未认证收到 `401`；
- [x] 岗位容量字段与当前有效成员一致，关闭项目仍保留成员数据；
- [x] migration upgrade/downgrade、ORM schema 和现有测试均通过。

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-12 | 创建堆叠任务分支 | 匹配接口必须先具备成员容量硬约束 |
| 2026-08-12 | 成员写入保持内部能力 | 防止绕过后续邀请接受与授权事务 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git fetch --prune origin` via `127.0.0.1:7897` | Passed | 前置提交 `2edb4b1` 已推送 |
| `python -m pytest -ra` with disposable MySQL 8.4 | Passed | 50 tests；包含真实 MySQL 并发争夺最后名额、持久化/API 与全部回归 |
| `python -m alembic check` against MySQL 8.4 | Passed | ORM 与 `20260812_0003` 无 schema 漂移 |
| `upgrade head -> downgrade base -> upgrade head` against MySQL 8.4 | Passed | 第三版复合外键、回滚顺序和重建通过；一次性容器已删除 |
| `python -m pytest -ra` without MySQL URL | Passed | 48 passed，3 个 MySQL 专属测试按配置跳过 |
| `python -m compileall -q app tests` | Passed | 应用与测试模块编译通过 |
| `git diff --check` | Passed | 无空白错误 |

## 10. 当前状态与下一步

- 最后完成：成员、容量、权限、迁移、文档与真实 MySQL 并发验证。
- 当前阻塞：无实现阻塞；等待角色 A 评审本分支及前置匹配偏好分支。
- 下一步：按依赖顺序评审后再合入；邀请模块在独立后续分支调用内部原子入队能力。
- 剩余风险：成员退出、踢出、换岗、owner 转移和邀请幂等均未实现，不能通过当前 API 操作。
- 最后相关提交：`feat(projects): add members and role capacity`
