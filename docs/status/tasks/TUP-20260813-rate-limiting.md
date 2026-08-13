# TUP-20260813-rate-limiting

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-rate-limiting`  
> Last Updated: 2026-08-13

## 目标

为认证、举报、邀请和消息发送接口增加可测试的服务端限流，降低凭证猜测、刷举报、邀请骚扰和消息洪泛风险。

## 范围

- 进程内固定窗口限流器，支持应用注入规则和测试时替换。
- 被限流时返回统一 `RATE_LIMITED` 错误及 `Retry-After` 响应头。
- 默认规则仅作为单实例/本地保护；多实例共享限流需要后续 Accepted ADR 与共享存储方案。

## 非目标

- 不新增 Redis 或其他生产依赖。
- 不信任客户端自报 IP，不改变现有鉴权、授权和数据模型。

## 影响接口

- `services/api/app/rate_limit.py`
- `make_app(..., rate_limiter=...)` 测试注入点
- API 429 错误响应头 `Retry-After`

## 验证记录

- [x] 限流器窗口、并发和过期行为测试
- [x] 登录接口 429 与 Retry-After 测试
- [x] 全量 API、迁移、SQL store 与真实 MySQL 8.4.11 测试（`python -m pytest -ra`: 80 passed）
- [x] `python -m compileall -q app`
- [x] `python -m pip check` 与项目级 `python -m pip_audit . --progress-spinner off`
- [x] `git diff --check`

## 评审说明

- 未新增依赖或数据库结构。
- 多实例生产部署仍需共享限流存储和 Accepted ADR；当前实现不能作为跨进程全局配额。
