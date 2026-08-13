# TUP-20260813-reports

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-reports`  
> Last Updated: 2026-08-13

## 目标

实现 SAFE-001 的用户举报提交链路：对用户、已公开项目和本人有权访问的消息创建待处理举报，避免泄露不可见资源，并对重复待处理举报幂等。

## 范围

- `ReportRequest`/`ReportData` DTO、MemoryStore/SQLAlchemyStore 与 Alembic 迁移。
- `POST /api/v1/reports`，服务端从会话确定 reporter，不接受客户端覆盖。
- 目标类型白名单、目标可见性/会话参与者检查、自己举报保护和受控原因。
- 重复的同一 reporter/target/reason 待处理举报返回原记录。

## 非目标

- 不实现管理员举报列表、审核、下架、封禁、申诉或审计后台。
- 不保存消息正文或自动从举报原文生成匹配/训练特征。
- 不引入独立限流组件；生产限流仍是部署与安全基线待办。

## 影响

- 接口：新增 `POST /api/v1/reports`。
- 数据：新增 `reports` 表，状态首版固定为 `PENDING`，为后续处置保留受控状态字段。
- 安全：不可见用户/项目/消息统一按资源不存在处理；消息举报要求 reporter 是会话参与者。

## 验证

- `python -m pytest -ra`（MySQL 8.4.11）：80 passed。
- `python -m alembic upgrade head / downgrade base / upgrade head`：迁移往返通过。
- `python -m compileall -q app tests migrations` 与 `git diff --check`：通过。
- 已覆盖迁移、API、Memory/SQL 幂等和消息参与者校验；补充目标账号进入待注销后，原举报重试仍幂等返回且不重复审计的回归验证。
