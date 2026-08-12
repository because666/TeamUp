# TUP-20260812-project-invitations 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/feature/TUP-20260812-project-invitations`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-12

## 1. 评审范围

- `POST /api/v1/invitations` 创建岗位邀请；
- `POST /api/v1/invitations/{invitationId}/accept` 接受并原子创建成员；
- `POST /api/v1/invitations/{invitationId}/reject` 拒绝邀请；
- owner/invitee 资源级授权与非 invitee 的 `404` 隐私反馈；
- 项目、岗位、容量、成员唯一性、过期和双向拉黑边界；
- 领域唯一键与状态机提供的重复请求保护；
- 首版服务端固定 7 天有效期。

## 2. 角色 A 验收清单

| ID | 验收项 | 预期行为 | 角色 A 结论 |
| --- | --- | --- | --- |
| INV-A-001 | 创建权限 | 只有项目 owner 可邀请，非 owner 返回 `403` | TBD |
| INV-A-002 | 目标与岗位 | 有效非本人用户、已发布项目、开放未满岗位才可邀请 | TBD |
| INV-A-003 | 重复创建 | 同项目/岗位/用户的有效待处理邀请返回原记录且不延长到期 | TBD |
| INV-A-004 | 有效期 | 服务端创建后 7 天过期，客户端不能指定或延长 | TBD |
| INV-A-005 | 处理权限 | 只有 invitee 可接受/拒绝；其他用户统一返回 `404` | TBD |
| INV-A-006 | 状态机 | 重复接受/拒绝幂等，终态不能相互转换 | TBD |
| INV-A-007 | 接受事务 | 并发接受不重复入队、不突破岗位容量 | TBD |
| INV-A-008 | 拉黑 | 任一方向拉黑后不能创建或接受邀请 | TBD |
| INV-A-009 | 范围边界 | 列表、通知、取消、限流、通用幂等和事件归因留待后续 | TBD |

## 3. 角色 B 验证证据

- API 测试覆盖未认证、owner、invitee、非 invitee、自邀、重复创建、接受和拒绝；
- SQLite 仓储覆盖持久化、过期替换、关闭项目、状态终态与权限；
- MySQL 8.4 覆盖真实持久化、重复创建、拉黑和双邀请并发争夺单人岗位；
- 初次真实并发测试暴露 MySQL `REPEATABLE READ` 旧快照导致超额，修正为写事务首个读取锁定项目后复验通过；
- 第五版迁移已验证 schema 无漂移及完整升级、回滚、重建。

## 4. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| Finding ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |

评审通过前不得合入 `main`。角色 A 需重点确认 7 天有效期与重复创建不续期行为是否符合前端交互。
