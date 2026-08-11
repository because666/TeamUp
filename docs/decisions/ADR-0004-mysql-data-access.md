# ADR-0004: MySQL 数据访问与迁移工具

> Status: Accepted<br>
> Decision Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Date: 2026-08-11

## Context

FastAPI 基础切片和微信登录目前使用进程内 `MemoryStore`，服务重启后用户、会话、名片和项目数据全部丢失，不能进入 staging/production。MySQL 已由项目确认，但 ORM、驱动、迁移和同步/异步边界仍未决定。

## Decision Drivers

- 与现有同步 FastAPI 路由和业务服务保持一致；
- 明确事务、乐观锁、唯一约束和外键；
- 支持 MySQL 8 的版本化迁移和回滚演练；
- 测试能够覆盖真实 MySQL，而不是只依赖 SQLite 行为；
- 双人团队容易维护、排查和审查；
- 不把数据库连接串、微信身份标识或 token 写入日志。

## Proposed Decision

采用：

- SQLAlchemy 2.x 同步 ORM；
- Alembic 迁移；
- PyMySQL 驱动；
- MySQL 8.0/8.4；
- FastAPI 普通同步路由/依赖执行阻塞数据库访问；
- 每个请求一个短生命周期 `Session`，业务写操作显式事务；
- 测试分为快速单元测试和真实 MySQL 集成测试。

首批物理表只覆盖现有可运行接口：

- `users`：内部用户、微信 subject、状态和时间；
- `sessions`：平台 token 摘要、用户、过期/撤销时间；
- `profiles`：能力名片和乐观锁版本；
- `profile_skills`、`profile_collaboration_scenarios`：结构化多值字段；
- `projects`：项目、owner、状态和乐观锁版本；
- `project_roles`、`project_role_skills`：岗位及技能。

平台 token 只以不可逆摘要存储；微信 `session_key`、AppSecret 和原始平台 token 不进入数据库。

## Alternatives

### SQLAlchemy async + asyncmy

优点是数据库等待期间可提高并发利用率；缺点是会把会话生命周期、事务、测试和调用链全部改为 async。当前业务规模和团队复杂度不足以证明收益。

### SQLModel

样板更少，但 API DTO 和持久化模型容易耦合，复杂约束和迁移最终仍落到 SQLAlchemy/Alembic。

### 原生 SQL / PyMySQL

控制直接，但映射、迁移和重复 CRUD 成本更高，不适合当前实体数量。

## Migration Strategy

1. 创建空库 schema 和约束，不迁移内存演示数据；
2. local/test 可显式选择 memory，staging/production 必须选择 MySQL；
3. 在测试 MySQL 验证 upgrade、约束、并发版本冲突和 downgrade；
4. 切换应用存储前保持 API 契约不变；
5. 首版迁移可完整 downgrade 到空 schema，不删除外部已有数据。

## Consequences

- 新增 SQLAlchemy、Alembic、PyMySQL 生产依赖；
- 数据库连接和事务仍是同步模型，不在请求处理内混用 async ORM；
- staging/production 不得退回内存存储；
- 后续消息与邀请模块可复用同一迁移和事务基线；
- 若真实负载证明同步连接池不足，必须通过后续 ADR 迁移异步栈。

## Approval

角色 B 于 2026-08-11 明确批准继续实施本方案。角色 A 仍需评审前端可见行为和契约兼容性。
