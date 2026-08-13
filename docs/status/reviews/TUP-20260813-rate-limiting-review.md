# TUP-20260813-rate-limiting 评审记录

> Status: Proposed  
> Reviewer: 角色 A  
> Review Target: `role-b/feature/TUP-20260813-rate-limiting`  
> Last Updated: 2026-08-13

## Evidence

- 实际命令和最新结果见对应任务文件；角色 A 评审时需独立核对。

## 待核对风险

- 当前计数器是进程内存，无法在多实例间共享；生产扩容前必须落地共享限流方案并通过 ADR。
- 登录限流按服务端连接地址计数；部署在受信任代理后应由部署配置保证连接地址不可被客户端伪造。
