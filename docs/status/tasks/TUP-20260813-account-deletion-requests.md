# TUP-20260813-account-deletion-requests

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-account-deletion-requests`  
> Last Updated: 2026-08-13

## 目标

实现 `API-AUTH-03` 的最小、可审计注销申请：账号进入 `DELETION_PENDING` 并撤销全部平台会话，不直接删除业务数据。

## 范围

- `POST /api/v1/account/deletion-requests` 与只读响应 DTO。
- MemoryStore/SQLAlchemyStore 一致的状态转换和全会话撤销。
- `account_deletion_requests` 迁移、待处理唯一键与状态约束。
- 并发/重复调用返回同一待处理申请；进入待注销状态后禁止重新登录和访问受保护资源。

## 非目标

- 不执行物理删除、匿名化、级联清理、恢复/取消申请或推荐派生数据清理。
- 不自行决定等待期、保留期、法定义务或通知渠道；这些仍是 `GAP-BE-PRIV-01`。

## 影响

- 接口：新增 `POST /api/v1/account/deletion-requests`。
- 数据：新增申请表；现有 `users.status` 已支持 `DELETION_PENDING`，无需改枚举。
- 安全：服务端只操作当前认证用户；成功后立即撤销该用户全部会话。

## 验证

- `python -m pytest -ra`（MySQL 8.4.11）：80 passed；覆盖申请后从人才发现、项目大厅、项目详情和匹配候选立即消失。
- `python -m alembic upgrade head / downgrade base / upgrade head`：迁移往返通过。
- `python -m compileall -q app tests migrations` 与 `git diff --check`：通过。
- `python -m pip check`：通过；`python -m pip_audit . --progress-spinner off`：项目依赖无已知漏洞。
- 覆盖多会话撤销、禁止重新登录、持久化状态、存储层重复申请及真实 MySQL 审计写入。

## 剩余风险

- 首次申请会立即撤销全部会话；若客户端在收到响应前断线，不能使用已撤销 token 重试 HTTP 请求。需要角色 A/B 在 `GAP-BE-PRIV-01` 中确认恢复查询或独立幂等键方案，当前不得宣称网络失败可恢复。
