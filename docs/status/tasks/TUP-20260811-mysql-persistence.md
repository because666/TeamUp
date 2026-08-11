# TUP-20260811-mysql-persistence: MySQL 持久化基础

> Status: Ready for Review<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `acd9ed3`<br>
> Branch: `role-b/feature/TUP-20260811-mysql-persistence`<br>
> Last Updated: 2026-08-11

## 1. 目标

将用户、会话、能力名片、项目和岗位从进程内存储迁移到可版本化、可测试的 MySQL 持久化层，且保持现有 API 契约不变。

## 2. 依据

- PRD：`BE-SYS-001`、`BE-AUTH-001/002`、`BE-PROF-001/002`、`BE-PROJ-001..005`
- API：`API-AUTH-01/02`、`API-PROF-01/02`、`API-PROJ-01..05`
- ADR：[ADR-0004](../../decisions/ADR-0004-mysql-data-access.md)

## 3. 范围

- 数据库配置、连接池、会话依赖和就绪检查；
- 首批 MySQL 表、唯一约束、外键、索引和 Alembic 迁移；
- 用户/会话/名片/项目存储接口和 SQLAlchemy 实现；
- token 摘要存储、撤销和过期校验；
- 单元、API、迁移和真实 MySQL 集成测试；
- 数据模型、迁移说明、开发命令和评审文件同步。

## 4. 非目标

- 不实现匹配、消息、邀请、举报或注销表；
- 不迁移 local memory 演示数据；
- 不在本任务部署生产数据库；
- 不修改前端字段和现有 URL。

## 5. 依赖与假设

- ADR-0004 必须先由角色 B 确认为 `Accepted`；
- 需要可访问的 MySQL 8 测试实例；当前 Docker CLI 存在，但未检测到可用 Docker/MySQL 服务；
- 数据库连接串只从环境/密钥服务读取，禁止进入仓库和日志；
- API 响应继续使用当前 camelCase DTO，数据库列采用 snake_case。

## 6. 计划

- [x] 接受 ADR-0004 并锁定依赖；
- [x] 建立 SQLAlchemy engine、session 和 repository 边界；
- [x] 创建 Alembic 初始迁移；
- [x] 实现 MySQL 用户、会话、名片和项目存储；
- [x] 替换路由中的全局 `MemoryStore` 依赖；
- [x] 验证真实 MySQL 迁移、约束、事务和并发；
- [x] 同步数据、开发和评审文档；API 契约未变化。

## 7. 验收标准

- [x] 服务重启后用户、会话、名片和项目仍存在；
- [x] 微信 subject 唯一，token 只存摘要；
- [x] 非 owner、过期/撤销 token、旧版本更新正确拒绝；
- [x] 初始迁移可从空库 upgrade 并可 downgrade；
- [x] staging/production 配置 memory 时拒绝启动；
- [x] 真实 MySQL 集成测试和现有 API 测试通过。

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-11 | 创建任务与 Proposed ADR | 按模块 procedure 进入持久化阶段 |
| 2026-08-11 | 接受 ADR-0004 并实现首批持久化 | 将内存适配器替换为可配置的 MySQL 生产适配器 |
| 2026-08-11 | 修复 MySQL 降级索引顺序与时间精度 | 真实 MySQL 8.4.11 验证暴露方言差异 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git fetch --prune origin` via `127.0.0.1:7897` | Passed | 基线包含 `acd9ed3` |
| `python -m pytest -ra` with `TEAMUP_TEST_MYSQL_URL` | Passed | 31 tests；MySQL 8.4.11 仓储/API 重启、SQLite 快速迁移/仓储和现有 API 回归 |
| `python -m compileall -q app tests` | Passed | 应用与测试模块编译通过 |
| `python -m alembic upgrade head` | Passed | MySQL 8.4.11 空库升级到 `20260811_0001` |
| `python -m alembic downgrade base` | Passed | MySQL 8.4.11 回滚到空业务 schema |
| `python -m alembic upgrade head --sql` | Passed | MySQL 方言离线 DDL 完整生成 |
| 并发 subject/名片验证 | Passed | 相同 subject 只有一个用户；并发首次名片保存一个成功、一个版本冲突 |
| Docker / MySQL | Passed | Docker Desktop；一次性 `mysql:8.4`，服务版本 8.4.11 |
| `git diff --check` | Passed | 无空白错误 |

## 10. 当前状态与下一步

- 最后完成：MySQL 首批表、迁移、仓储选择、真实数据库验证和文档同步。
- 当前阻塞：无实现阻塞；进入角色 A 契约兼容性评审。
- 下一步：角色 A 在 `docs/status/reviews/TUP-20260811-mysql-persistence-review.md` 记录结论；评审通过后再提交集成到 `main`。
- 最后相关提交：本任务提交 `feat(database): add MySQL persistence foundation`
