# TUP-20260812-project-invitations: 项目岗位邀请与接受事务

> Status: Ready for Review<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `1b0b399`<br>
> Branch: `role-b/feature/TUP-20260812-project-invitations`<br>
> Last Updated: 2026-08-12

## 1. 目标

让项目 owner 可向有效用户发送岗位邀请，并让被邀请者安全、幂等地接受或拒绝；接受邀请在单一事务内创建唯一成员关系且不得突破岗位容量或拉黑边界。

## 2. 依据

- PRD：`TEAM-001`、`NFR-REL-001`；
- 后端 PRD：`BE-TEAM-001/002/003`、`BE-GOAL-003`、`BE-SEC-008`、`BE-E2E-007`；
- API：`API-TEAM-01/02/03`；
- ADR：N/A；邀请状态机和事务边界已由现有 PRD、API 与数据规范定义。

## 3. 范围

- `invitations` ORM、第五版 Alembic 迁移和 memory/SQL repository；
- `POST /api/v1/invitations`、`POST /api/v1/invitations/{invitationId}/accept`、`POST /api/v1/invitations/{invitationId}/reject`；
- owner、invitee 和资源级授权，项目/岗位/用户状态、容量、成员唯一性、过期与双向拉黑检查；
- 创建邀请和处理邀请的幂等行为；
- 接受邀请与成员写入的单事务/并发约束；
- API、数据、安全、迁移、状态和角色 A 评审文档同步。

## 4. 非目标

- 不实现邀请列表、详情、取消、主动申请或管理员代处理；
- 不实现定时过期任务；读取或处理时按 `expires_at` 判断过期；
- 不发送微信订阅消息、站内通知或邮件；
- 不实现邀请限流、举报、审计后台或推荐事件归因；
- 不合入 `main`，直到角色 A 评审。

## 5. 依赖与假设

- 本任务堆叠在已推送的拉黑提交 `1b0b399` 上；
- `PENDING -> ACCEPTED | REJECTED` 由本模块实现；`EXPIRED` 通过服务端时间判定，`CANCELLED` 留给后续取消接口；
- 同一项目/岗位/被邀请者最多一条 `PENDING` 邀请；重复创建返回原邀请，不延长到期时间；
- 接受已 `ACCEPTED` 的本人邀请幂等返回原结果；其他已处理、过期或不可接受状态返回 `INVITATION_NOT_ACTIONABLE`；
- 拒绝已 `REJECTED` 的本人邀请幂等返回原结果；不能把已接受邀请改为拒绝；
- 当前没有独立 `Idempotency-Key` 持久化表，领域唯一键与状态机提供本任务所需的重复请求保护；如后续要求跨 payload key 重放，再建立通用幂等模块；
- 2026-08-12 首次远程同步尝试经 `127.0.0.1:7897` 失败；本地基线与已推送远程跟踪引用均为 `1b0b399`，提交前必须重试 fetch。

## 6. 计划

- [x] 创建独立分支和任务文件，固定状态机、接口与非目标；
- [x] 实现 DTO、repository、ORM 和第五版迁移；
- [x] 实现创建、接受、拒绝接口和资源级授权；
- [x] 增加内存、SQLite、MySQL、迁移和并发测试；
- [x] 同步契约、数据、安全、任务和角色 A 评审文件；
- [x] 完整验证和复查；提交并推送在验证后执行。

## 7. 验收标准

- [x] 只有项目 owner 可针对自己已发布项目的开放且未满岗位邀请有效用户；
- [x] 双向拉黑、已有成员、无效用户、关闭项目或岗位、满员岗位均不能创建邀请；
- [x] 只有 invitee 可接受或拒绝自己的邀请，未认证和 IDOR 请求不泄露敏感资源；
- [x] 接受操作在单一事务内重新检查状态、过期、拉黑、成员唯一和岗位容量；
- [x] 重复/并发创建或接受不产生重复邀请、重复成员或超额成员；
- [x] API、数据、安全、迁移与评审文档同步，测试和静态检查通过。

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-12 | 创建堆叠任务分支 | 邀请依赖成员容量和统一拉黑查询 |
| 2026-08-12 | 使用领域唯一键提供重复保护 | 当前范围无需新增通用幂等依赖或公共架构 |
| 2026-08-12 | 接受事务以项目行锁作为首个写事务读取 | 避免 MySQL `REPEATABLE READ` 旧快照让并发接受突破容量 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git fetch --prune origin` via `127.0.0.1:7897` | Failed | 首次代理端口拒绝连接；提交前重试 |
| final `git fetch --prune origin` via `127.0.0.1:7897` | Passed | 提交前远程引用同步成功 |
| `python -m pytest -ra` without MySQL URL | Passed | 54 passed，5 个 MySQL 专属测试按配置跳过 |
| `python -m pytest -ra` with disposable MySQL 8.4 | Passed | 59 passed；覆盖邀请持久化、拉黑、关闭项目和双邀请并发容量 |
| `python -m alembic check` against MySQL 8.4 | Passed | ORM 与第五版迁移无 schema 漂移 |
| `upgrade head -> downgrade base -> upgrade head` against MySQL 8.4 | Passed | 第五版迁移、约束、回滚和重建通过；一次性容器已删除 |
| `python -m compileall -q app tests` | Passed | 应用与测试模块编译通过 |
| changed Markdown relative-link check | Passed | 8 个变更 Markdown 文件的相对链接均有效 |
| `git diff --check` | Passed | 无空白错误 |

## 10. 当前状态与下一步

- 最后完成：三条邀请 API、第五版迁移、状态机、双向拉黑接入及 MySQL 并发容量修复。
- 当前阻塞：无实现阻塞；7 天有效期与不续期行为等待角色 A 评审。
- 下一步：推送任务分支并由角色 A 按独立评审文件验收。
- 剩余风险：未实现邀请列表、通知、取消、限流、通用 `Idempotency-Key`、审计和推荐事件归因。
- 最后相关提交：`uncommitted`
