# TUP-20260812-user-blocks 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/feature/TUP-20260812-user-blocks`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-12

## 1. 评审范围

- `POST /api/v1/blocks` 和 `DELETE /api/v1/blocks/{blockedUserId}`；
- 重复拉黑与重复取消的幂等反馈；
- 禁止自己拉黑、目标不存在和未认证错误；
- 不暴露对方是否反向拉黑、原因或关系列表；
- 拉黑立即阻止后续新成员创建，但不删除既有成员或历史数据；
- 后续消息、邀请、发现和匹配必须复用双向阻断查询。

## 2. 角色 A 验收清单

| ID | 验收项 | 预期行为 | 角色 A 结论 |
| --- | --- | --- | --- |
| BL-A-001 | 拉黑成功 | 返回目标 opaque ID 和首次创建时间 | TBD |
| BL-A-002 | 重复拉黑 | `200` 幂等返回原关系，不重复创建 | TBD |
| BL-A-003 | 取消拉黑 | 删除自己的单向关系；不存在时 `removed=false` | TBD |
| BL-A-004 | 隐私 | 不返回原因、对方操作或反向拉黑状态 | TBD |
| BL-A-005 | 立即阻断 | 任一方向存在关系时阻止新成员，后续消息/邀请/匹配复用 | TBD |
| BL-A-006 | 历史数据 | 不自动删除既有成员、会话、邀请或消息 | TBD |
| BL-A-007 | 前置依赖 | 本分支堆叠在成员提交 `3cb85a2` 上，需按顺序评审 | TBD |

## 3. 角色 B 验证证据

- API 测试覆盖未认证、自拉黑、目标不存在、重复创建和重复删除；
- Memory/SQLite/MySQL 覆盖双向查询、持久化和成员创建阻断；
- 数据库主键与 check constraint 阻止重复和自己拉黑；
- 真实 MySQL 与迁移验证结果以任务文件最终记录为准。

## 4. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| Finding ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |

评审通过前不得合入 `main`。举报、拉黑列表、消息、邀请、发现和匹配接入均属于后续独立任务。
