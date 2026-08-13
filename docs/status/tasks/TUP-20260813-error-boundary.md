# TUP-20260813-error-boundary

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-error-boundary`  
> Last Updated: 2026-08-13

## 目标

为未预期的服务端异常建立统一脱敏边界，避免内部异常文本进入 API 响应，同时保留稳定的 `INTERNAL_ERROR` 错误码和 request ID。

## 范围

- FastAPI 全局未知异常处理器。
- 回归测试覆盖异常响应内容和 request ID。
- 不改变已定义的业务异常、HTTP 状态码或数据模型。

## 非目标

- 不在响应中返回堆栈、数据库错误、环境变量或异常原文。
- 不新增日志供应商、追踪后端或生产依赖。

## 验证项

- [x] 未预期异常返回统一 500 `INTERNAL_ERROR`
- [x] 业务异常和参数校验仍使用原有错误码（全量回归通过）
- [x] 全量测试、编译检查和 diff 检查

## 验证记录

- `python -m pytest -ra`（MySQL 8.4.11）: 80 passed
- `python -m compileall -q app tests migrations`: passed
- `git diff --check`: passed

## 剩余风险

- 测试环境使用 `raise_server_exceptions=False` 验证 HTTP 脱敏响应；生产日志供应商和告警策略仍属于部署阶段范围。
