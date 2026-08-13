# TUP-20260813-readiness-boundary

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-readiness-boundary`  
> Last Updated: 2026-08-13

## 目标

将存储依赖异常统一映射为健康检查的 `503 DEPENDENCY_NOT_READY`，避免就绪探针误报或泄露内部连接错误。

## 范围

- `/api/v1/health/ready` 捕获 store readiness 异常并返回稳定业务错误。
- 回归测试覆盖异常、脱敏和 request ID。

## 非目标

- 不改变存活探针 `/health/live`。
- 不改变业务接口错误映射、数据库连接策略或部署探针路径。

## 验证记录

- `python -m pytest -ra`（MySQL 8.4.11）: 80 passed
- `python -m compileall -q app tests migrations`: passed
- `git diff --check`: passed

## 剩余风险

就绪探针只反映当前 store 的连接可用性；外部微信服务、异步任务和部署级依赖仍需在 staging 阶段单独探测。
