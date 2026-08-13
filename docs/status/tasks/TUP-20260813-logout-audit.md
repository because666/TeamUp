# TUP-20260813-logout-audit

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-logout-audit`  
> Last Updated: 2026-08-13

## 目标

补齐退出登录的最小安全审计：成功撤销当前会话时记录 actor、动作、资源类型、request ID 和结果，不记录 token。

## 范围

- MemoryStore 与 SQLAlchemyStore 的 logout 审计。
- API 退出路由传递 request ID。
- 回归测试覆盖成功退出、重复退出和 token 不进入审计记录。

## 非目标

- 不改变退出接口响应结构。
- 不记录 bearer token、token digest 或客户端 IP。

## 验证项

- [x] memory/sql logout 审计
- [x] API 回归测试
- [x] 全量测试、编译和 diff 检查

## 验证记录

- `python -m pytest -ra`（MySQL 8.4.11）: 80 passed
- `python -m compileall -q app tests migrations`: passed
- `git diff --check`: passed

## 剩余风险

- 重复退出已保持幂等，但只对实际存在且未撤销的会话写成功审计事件；无效 token 不写 actor 审计，避免伪造资源关联。
