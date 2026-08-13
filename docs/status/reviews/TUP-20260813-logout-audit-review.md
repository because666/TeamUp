# TUP-20260813-logout-audit 评审记录

> Status: Proposed  
> Reviewer: 角色 A  
> Review Target: `role-b/feature/TUP-20260813-logout-audit`  
> Last Updated: 2026-08-13

## Evidence

- 实际命令和最新结果见对应任务文件；角色 A 评审时需独立核对。

## Result

退出成功时在 memory/SQL 两个存储实现中记录 `LOGOUT` 审计事件，使用 request ID 关联请求；token 明文和 digest 均不进入审计事件或 API 响应。

## 剩余风险

后台审计查询、保留周期和管理员权限仍属于 `GAP-BE-SAFE-01` / `GAP-BE-PRIV-01`，本切片不擅自实现。
