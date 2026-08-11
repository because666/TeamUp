# TUP-20260811-wechat-login: 微信真实登录

> Status: Proposed<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `12f49b8`<br>
> Branch: `role-b/feature/TUP-20260811-wechat-login`<br>
> Last Updated: 2026-08-11

## 1. 目标

将现有 `/api/v1/auth/wechat/login` 的 local/test 替代登录扩展为真实微信小程序 code 换取，并保持前端可见的会话响应契约不变。

## 2. 范围

- 服务端从环境变量读取 `WECHAT_APP_ID`、`WECHAT_APP_SECRET`、可选代理、接口地址和超时时间。
- 使用微信 `jscode2session` 换取 `openid`，只将其用于内部用户映射；不持久化或返回 `session_key`。
- 将微信错误、超时、畸形响应映射为稳定的服务端错误码。
- 保留明确标记的 `local:<subject>` 替代登录，仅允许 local/test。
- 增加 Mock 外部 HTTP 测试、配置缺失测试和会话响应测试。

## 3. 非目标

- 不在本任务中实现 MySQL 用户表、刷新令牌、微信手机号解密或生产密钥部署。
- 不把 `session_key` 写入日志、数据库、响应或客户端存储。

## 4. 验收标准

- 有效微信 code 在配置完整时创建/复用内部用户并返回现有 `SessionData`。
- `consentAccepted=false` 在调用微信前被拒绝。
- 微信 `errcode`、超时、网络错误和缺少 `openid` 均不会伪造登录成功。
- 真实配置只通过服务端环境变量注入，`.env.example` 不含真实值。
- `python -m pytest`、`python -m compileall -q app tests` 和 OpenAPI 生成通过。

## 5. 变更文件

- `services/api/app/config.py`
- `services/api/app/wechat.py`
- `services/api/app/main.py`
- `services/api/pyproject.toml`
- `services/api/.env.example`
- `services/api/tests/test_api.py`
- `services/api/tests/test_wechat.py`
- `docs/architecture/API_CONTRACT.md`
- `docs/development/DEVELOPMENT.md`

## 6. 验证记录

| Check | Result | Evidence |
| --- | --- | --- |
| Baseline fetch through `127.0.0.1:7897` | Passed | Remote baseline `12f49b8` available |
| `python -m pytest` | Passed | 23 tests passed |
| `python -m compileall -q app tests` | Passed | Bytecode compilation succeeded |
| OpenAPI generation | Passed | Login response remains typed `Envelope[SessionData]` |
| Uvicorn health smoke test | Passed | `127.0.0.1:8000/api/v1/health/live` returned HTTP 200 |
| External WeChat call | Not run | Requires user-provided server-side credentials; Mock transport covers behavior |
