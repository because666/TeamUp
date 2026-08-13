# TUP-20260813-ci-contract-gate

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-ci-contract-gate`  
> Last Updated: 2026-08-13

## 目标

为后端建立可重复的 CI 门禁，并用测试校验 OpenAPI 路由与统一响应/错误契约的关键边界。

## 范围

- GitHub Actions 后端测试工作流。
- CI 隔离 MySQL 8.4 service、迁移到 head 后执行全部数据库专项测试。
- OpenAPI 路由清单与响应模型回归测试。
- 使用仓库已锁定的 Python 依赖和命令。

## 非目标

- 不连接生产数据库、微信服务或真实密钥；CI 数据库凭据只用于 job 生命周期内的一次性 service container。
- 不改变公共 API 路径、DTO 或数据模型。

## 验证项

- [x] OpenAPI 契约测试
- [x] CI 命令在本地实际运行
- [x] YAML/代码差异检查

## 验证记录

- `python -m pytest -ra`（MySQL 8.4.11）: 80 passed
- `python -m compileall -q app tests migrations`: passed
- `python -m pip check`: passed，已安装依赖无冲突
- `python -m pip_audit . --progress-spinner off`: passed，项目 `pyproject.toml` 解析结果无已知漏洞
- `git diff --check`: passed
- MySQL service workflow 与本地等价步骤：MySQL 8.4.11、`alembic upgrade head`、80 passed
- OpenAPI 门禁逐项校验 32 个公开 method/path 组合与成功响应声明
- ASGI smoke test (`uvicorn` + `httpx`, `GET /api/v1/health/live`, `trust_env=False`): HTTP 200，`data.status=ok`

## 剩余风险

- CI 工作流未在 GitHub runner 上实际执行；本地使用同一组命令完成验证。
- workflow 已配置隔离 MySQL 8.4 service，但尚未在 GitHub runner 实际执行；首次 push 后必须查看 Actions 结果，不能用本地验证冒充远端门禁通过。
