# TUP-20260811-fastapi-backend：FastAPI 后端决策、PRD 与初始化准备

> Status: In Progress<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `b19c209`<br>
> Branch: `role-b/feature/TUP-20260811-backend-foundation`<br>
> Last Updated: 2026-08-11

## 验证证据

- 通过 `127.0.0.1:7897` 代理执行 `python -m pip install -e ".[test]"`：通过。
- 在 `services/api` 执行 `python -m pytest`：通过，5 个测试。
- 执行 `python -m compileall -q app tests`：通过。
- 生成 OpenAPI：通过，共 9 条路径。
- 在 `127.0.0.1:8000` 执行 Uvicorn 冒烟测试：`/api/v1/health/live` 返回 HTTP 200。
- 范围限制：当前仅支持 local/test 内存持久化；MySQL 迁移和其余 P0 接口待完成。

## 1. 目标

将角色 B 对 FastAPI 的明确选择写入仓库真值，形成可拆分任务和验收的完整后端 PRD，并为下一任务的 FastAPI 纵向验证和正式工程初始化解除框架决策阻塞。

## 2. 依据

- 用户明确决定：后端选择 FastAPI（2026-08-11）
- ADR：[ADR-0001](../../decisions/ADR-0001-backend-framework.md)
- 架构：[ARCHITECTURE.md](../../architecture/ARCHITECTURE.md)
- 开发：[DEVELOPMENT.md](../../development/DEVELOPMENT.md)

## 3. 范围

- 将 ADR-0001 更新为 `Accepted`，选择 FastAPI；
- 同步 README、架构、开发、对接、ADR 索引和当前状态；
- 新增角色 A 的契约与用户可见影响评审入口；
- 新增 `docs/product/BACKEND_PRD.md`，覆盖 P0/P1 范围、权限、通用 API、26 个接口对应行为、数据、安全、测试、部署、交付阶段和缺口；
- 更新产品 PRD 与文档索引，明确权威边界，避免复制出第二套 API 真值；
- 明确具体 Python/FastAPI 版本、依赖管理、数据访问、迁移和异步策略仍待纵向验证；
- 记录下一工程初始化任务的验证范围。

## 4. 非目标

- 不创建 `services/api` 或任何业务代码；
- 不选择 ORM、迁移工具、依赖管理器、ASGI 服务器或认证实现；
- 不修改 API DTO、数据库 schema、权限模型或部署拓扑；
- 不 commit、push、merge 或部署。

## 5. 依赖与假设

- 当前本地基线为 `b19c209`；
- `git fetch --prune origin` 已于 2026-08-11 重试成功，远程目标基线无新增提交；
- FastAPI 选择由角色 B 明确确认；角色 A 仍需评审契约和用户可见影响；
- 工具链只有在纵向验证实际通过后才能写入开发指南。

## 6. 计划

- [x] 记录 FastAPI 框架决定
- [x] 同步架构、开发、对接和状态文档
- [x] 编写完整后端 PRD 和需求追踪矩阵
- [x] 登记前端产品规格中的后端契约缺口
- [ ] 角色 A 完成契约和用户可见影响评审
- [ ] 新建后端初始化任务，完成不超过半天的纵向验证

## 7. 验收标准

- [x] ADR-0001 明确选择 FastAPI 并说明未决工具链
- [x] 仓库中不再把 FastAPI / Spring Boot 表述为未决二选一
- [x] 未虚构版本、命令、测试或工程目录已经可用
- [x] 后端 P0 功能、权限、数据、安全、测试和里程碑具有稳定 ID 与验收标准
- [ ] 角色 A 给出 `Approved` 或 `Changes Requested`

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-11 | 选择 FastAPI | 角色 B 明确确认后端框架 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git fetch --prune origin` | Passed | 首次超时，重试成功；远程目标基线无新增提交 |
| 文档一致性与相对链接 | Passed | 无旧框架二选一结论残留；相对链接目标全部存在 |
| `git diff --check` | Passed | 无 whitespace error |
| 敏感信息检查 | Passed | 常见 API key、云密钥和私钥模式无命中 |
| 后端 PRD 需求 ID | Passed | 31 个 `BE-*` 需求定义均唯一 |
| API 追踪完整性 | Passed | API 契约中的 26 个 API ID 全部在后端 PRD 中出现 |
| 后端构建/测试 | Not run | 后端工程尚未初始化，本任务仅记录决策 |

## 10. 当前状态与下一步

- 最后完成：FastAPI 决策、完整后端 PRD、需求追踪、评审入口和受影响索引已同步。
- 当前阻塞：无；具体工具链等待纵向验证。
- 下一步：角色 A 评审本次决策影响；角色 B 新建 FastAPI 初始化任务并执行纵向验证。
- 最后相关提交：`uncommitted`
