# TUP-20260811-mysql-persistence 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/feature/TUP-20260811-mysql-persistence`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-11

## 1. 评审范围

- 登录、名片和项目接口的 URL、请求、响应及错误码保持兼容；
- 服务重启后用户、会话、名片和项目数据仍可读取；
- local/test 可继续使用 memory，staging/production 必须使用 MySQL；
- 原始平台 token、微信 `session_key`、AppSecret 和数据库连接串不进入业务表、响应或日志；
- 角色 A 的前端 mock 和现有字段不需要因本任务修改。

## 2. 验证证据

- 自动化测试：31 个通过，包含真实 MySQL 8.4.11 仓储与 API 重启集成测试；
- MySQL Alembic：`upgrade head -> downgrade base -> upgrade head` 通过；
- 并发验证：相同微信 subject 收敛到一个用户，并发首次名片保存只有一个成功；
- 持久化验证：重建仓储后会话、名片和项目仍可读取；
- 安全验证：数据库只保存 token SHA-256 摘要，撤销和过期 token 被拒绝；
- Python 编译与 `git diff --check`：通过。

## 3. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |
