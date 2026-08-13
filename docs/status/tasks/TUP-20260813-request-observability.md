# TUP-20260813-request-observability

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-request-observability`  
> Last Updated: 2026-08-13

## 目标

补齐 BE-SYS-002 的最小请求可观测性：每个 HTTP 请求输出一条可机器解析的完成日志，并可用 request ID 串联业务响应和审计事件。

## 范围

- 结构化记录事件名、request ID、HTTP method、path、status 与 durationMs。
- 对客户端 request ID 做长度和字符白名单校验；不安全值由服务端替换。
- 测试证明 bearer token、query string 和请求体正文不进入请求日志。

## 非目标

- 不决定日志供应商、采集拓扑、保留期、告警阈值或 trace 后端。
- 不记录用户资料、消息/举报正文、微信 code、密钥、Authorization 或数据库连接串。

## 验证

- `python -m compileall -q app migrations`：通过。
- 请求日志脱敏测试：通过。
- `python -m pytest -ra`（MySQL 8.4.11）：80 passed。
- `python -m compileall -q app tests migrations` 与 `git diff --check`：通过。
