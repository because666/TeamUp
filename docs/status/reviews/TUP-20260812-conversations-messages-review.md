# TUP-20260812-conversations-messages 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/feature/TUP-20260812-conversations-messages`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-12

## 1. 评审范围

- `POST/GET /api/v1/conversations` 创建/列出项目双人会话；
- `GET/POST /api/v1/conversations/{conversationId}/messages` 分页读取/发送纯文本；
- 会话必须绑定已发布项目，且双方至少一人是项目 owner 或有效成员；
- 项目/用户组合唯一、sender 范围 `clientMessageId` 幂等；
- 参与者授权、非参与者 `404`、双向拉黑和历史消息可见性；
- 会话倒序和消息正序的服务端不透明 cursor 分页；
- 消息正文敏感数据与非目标边界。

## 2. 角色 A 验收清单

| ID | 验收项 | 预期行为 | 角色 A 结论 |
| --- | --- | --- | --- |
| MSG-A-001 | 会话上下文 | 绑定 `PUBLISHED` 项目，双方至少一人是 owner/有效成员 | TBD |
| MSG-A-002 | 双向发起 | owner 联系人才、候选人联系项目方都可创建 | TBD |
| MSG-A-003 | 会话唯一 | 同项目和同一对用户重复创建返回同一会话 | TBD |
| MSG-A-004 | 列表摘要 | 只列自己的会话，不返回消息正文，最近活动优先 | TBD |
| MSG-A-005 | 读取权限 | 只有参与者可读消息，其他用户统一 `404` | TBD |
| MSG-A-006 | 文本约束 | 去空白后 1..1000 字符，只支持 `TEXT` | TBD |
| MSG-A-007 | 发送幂等 | sender 范围同 key 同正文返回原消息，不同正文冲突 | TBD |
| MSG-A-008 | 拉黑 | 阻止新会话/新消息，不删除原参与者历史消息 | TBD |
| MSG-A-009 | 分页 | 会话倒序、消息正序，cursor 不透明且无重复遗漏 | TBD |
| MSG-A-010 | 非目标 | 已读、未读、附件、撤回、通知、WebSocket、限流不在本次 | TBD |

## 3. 角色 B 验证证据

- API 测试覆盖认证、双向发起、自聊、参与者/非参与者、校验、幂等、拉黑和 OpenAPI；
- SQLite 仓储覆盖会话/消息持久化、会话列表分页、消息分页、非法 cursor 和重建读取；
- 数据库复合外键保证消息 sender 是该会话参与者，唯一键保证 sender/client ID 唯一；
- MySQL 8.4 覆盖并发创建同一会话、同 key 同正文重放和同 key 不同正文冲突；
- 第六版迁移已验证 schema 无漂移及完整升级、回滚、重建。

## 4. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| Finding ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |

评审通过前不得合入 `main`。角色 A 需重点确认会话上下文、1000 字符上限、消息排序方向和拉黑后历史消息仍可读的前端体验。
