# TUP-20260812-conversations-messages: 双人会话与文本消息

> Status: Ready for Review<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `f3bf931`<br>
> Branch: `role-b/feature/TUP-20260812-conversations-messages`<br>
> Last Updated: 2026-08-12

## 1. 目标

让已认证用户可围绕已发布项目建立唯一双人会话，列出自己的会话，并在参与者授权、双向拉黑和幂等约束下分页读取或发送纯文本消息。

## 2. 依据

- PRD：`MSG-001`、`NFR-SEC-001/002`、`NFR-REL-001`；
- 后端 PRD：`BE-MSG-001/002/003`、`BE-SEC-008`、`BE-E2E-006`；
- API：`API-CONV-01/02`、`API-MSG-01/02`；
- ADR：N/A；现有 PRD/API/安全规范已定义参与者授权、稳定分页和拉黑阻断。

## 3. 范围

- `conversations`、`conversation_participants`、`messages` ORM 与第六版 Alembic 迁移；
- `POST /api/v1/conversations` 创建或取得双人项目会话；
- `GET /api/v1/conversations` 列出当前用户会话；
- `GET /api/v1/conversations/{conversationId}/messages` 稳定游标分页；
- `POST /api/v1/conversations/{conversationId}/messages` 发送纯文本消息；
- 参与者资源级授权、项目状态、有效用户、双向拉黑与消息幂等；
- memory/SQL/MySQL/迁移测试和共享文档、角色 A 评审入口同步。

## 4. 非目标

- 不实现群聊、附件/图片、富文本、系统消息、引用、编辑、撤回、删除或反应；
- 不实现已读回执、未读数、输入状态、在线状态、推送通知或 WebSocket；
- 不自动从邀请或匹配事件创建会话；
- 不实现会话退出/归档、管理员读消息、内容审核后台、限流或消息保留清理；
- 不合入 `main`，直到角色 A 评审。

## 5. 依赖与假设

- 本任务堆叠在已推送邀请提交 `f3bf931` 上；
- 首版每个会话固定两名参与者，并绑定一个 `PUBLISHED` 项目；两名参与者中至少一人必须是项目 owner 或该项目有效成员，另一参与者必须是有效用户；
- 会话唯一键由 `project_id + sorted(user_id pair)` 构成，重复创建返回原会话；
- 消息请求必须携带客户端生成的 `clientMessageId`，同一 sender 范围内唯一；同 key 同正文返回原消息，不同正文返回 `MESSAGE_IDEMPOTENCY_CONFLICT`；
- 消息最大 1000 字符，去除首尾空白后不得为空；只保存纯文本；
- 会话列表按最近消息时间/创建时间倒序；消息按 `(created_at, id)` 正序，cursor 为服务端 base64url 不透明值；每页默认 20、最大 50；
- 拉黑立即阻止新会话和新消息，但不删除或隐藏双方历史消息；
- 以上 DTO、唯一性、分页和长度属于角色 B 的 `Proposed` 实现，需要角色 A 评审。

## 6. 计划

- [x] 创建独立任务分支与任务文件；
- [x] 核对消息相关 PRD、API、数据、安全规范和现有仓储模式；
- [x] 实现 DTO、ORM、memory/SQL repository 和第六版迁移；
- [x] 实现会话创建/列表与消息分页/发送接口；
- [x] 增加授权、拉黑、幂等、分页、持久化和 MySQL 并发测试；
- [x] 同步产品、API、数据、安全、迁移、状态和评审文档；
- [x] 完整验证和复查；提交并推送在验证后执行。

## 7. 验收标准

- [x] 只有合格发起者可为已发布项目创建双人会话，重复创建返回同一会话；
- [x] 只有参与者可列出/读取/发送，非参与者不获知私有会话或消息是否存在；
- [x] 任一方向拉黑后不能创建新会话或发送新消息，历史消息仍可由原参与者读取；
- [x] 空白、超长或幂等键冲突消息被显式拒绝，不写入重复消息；
- [x] 会话列表和消息游标分页稳定，无重复或遗漏；
- [x] MySQL 并发同 key 发送只产生一条消息；
- [x] API、数据、安全、迁移、任务与评审文档同步，全部检查通过。

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-12 | 创建堆叠任务分支 | 沟通闭环依赖已完成的拉黑与项目成员基础 |
| 2026-08-12 | 采用双人项目会话与 sender 范围消息幂等键 | 保持 MVP 边界并为弱网重试提供确定结果 |
| 2026-08-12 | 项目关联方可作为任一方 | 同时支持 owner 联系人才和候选人联系项目方 |
| 2026-08-12 | 已成功同 key 重试先于拉黑检查 | 网络重放返回原确定结果，不构成新消息写入 |
| 2026-08-12 | 正文长度由 API/服务层校验 | MySQL/SQLite 字符长度函数语义不同，避免中文被按字节误拒绝 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git fetch --prune origin` via `127.0.0.1:7897` | Passed | 基线 `f3bf931` 已同步 |
| `python -m pytest -ra` without MySQL URL | Passed | 56 passed，6 个 MySQL 专属测试按配置跳过 |
| `python -m pytest -ra` with disposable MySQL 8.4 | Passed | 62 passed；覆盖并发会话唯一、消息重放/冲突、持久化和完整回归 |
| `python -m alembic check` against MySQL 8.4 | Passed | ORM 与第六版迁移无 schema 漂移 |
| `upgrade head -> downgrade base -> upgrade head` against MySQL 8.4 | Passed | 第六版迁移、复合外键、回滚和重建通过；一次性容器已删除 |
| `python -m compileall -q app tests` | Passed | 应用与测试模块编译通过 |
| changed Markdown relative-link check | Passed | 10 个变更 Markdown 文件的相对链接均有效 |
| `git diff --check` | Passed | 无空白错误 |

## 10. 当前状态与下一步

- 最后完成：四条会话/消息 API、第六版迁移、权限/拉黑/幂等/稳定分页和真实 MySQL 并发验证。
- 当前阻塞：无实现阻塞；会话上下文、1000 字符上限、分页方向与历史可见性等待角色 A 评审。
- 下一步：推送任务分支并由角色 A 按独立评审文件验收。
- 剩余风险：未实现已读/未读、附件、撤回、通知、WebSocket、限流、内容治理和消息保留策略。
- 最后相关提交：`uncommitted`
