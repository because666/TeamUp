# TUP-20260813-rate-limit-cleanup

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-rate-limit-cleanup`  
> Last Updated: 2026-08-13

## 目标

防止单进程固定窗口限流器长期运行时因大量一次性 key 导致内存无界增长。

## 范围

- 在检查请求时清理已完全过期的窗口。
- 提供可测试的清理方法和过期窗口测试。
- 不改变现有默认限流规则和 API 错误契约。

## 非目标

- 不把进程内限流器宣称为多实例全局限流。
- 不新增 Redis 或其他生产依赖。

## 验证项

- [x] 过期 key 自动清理
- [x] 清理不影响当前窗口计数
- [x] 全量测试、编译和 diff 检查

## 验证记录

- `python -m pytest -ra`（MySQL 8.4.11）: 80 passed
- `python -m compileall -q app tests migrations`: passed
- `git diff --check`: passed

## 剩余风险

当前仍是单进程限流；多实例全局配额需要共享存储方案和 Accepted ADR。
