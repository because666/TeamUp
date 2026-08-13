# TUP-20260813-audit-events

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-audit-events`  
> Last Updated: 2026-08-13

## 目标

为当前已实现的高风险/数据权利操作建立最小审计记录，使举报提交和注销申请可按服务端 request ID 追溯。

## 范围

- 新增 `audit_events` 表与 MemoryStore 对等记录。
- 举报首次创建记录 `REPORT_SUBMITTED`；注销申请首次创建记录 `ACCOUNT_DELETION_REQUESTED`。
- 审计写入与对应 SQL 业务操作位于同一事务，幂等重试不重复创建事件。
- HTTP request ID 只接受有限长度安全字符；无效客户端值由服务端重新生成。

## 非目标

- 不开放普通用户审计查询；不实现管理员审计 API、日志导出或长期归档。
- 不记录举报说明、消息正文、token、微信凭证、密钥或数据库连接信息。

## 验证

- `python -m pytest -ra`（MySQL 8.4.11）：80 passed。
- `python -m alembic upgrade head / downgrade base / upgrade head`：迁移往返通过。
- `python -m compileall -q app tests migrations` 与 `git diff --check`：通过。
- 已覆盖 request ID 白名单、同事务写入与幂等重试不重复审计，并在真实 MySQL 验证举报和注销审计持久化。
