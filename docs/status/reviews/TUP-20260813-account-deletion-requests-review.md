# TUP-20260813-account-deletion-requests 评审记录

> Status: Proposed  
> Reviewer: 角色 A  
> Review Target: `role-b/feature/TUP-20260813-account-deletion-requests`  
> Last Updated: 2026-08-13

## 待评审范围

- 注销申请后立即撤销全部会话并阻止重新登录的用户行为。
- `DELETION_PENDING` 状态与待处理申请唯一键。
- 与未来等待期、取消、最终删除/匿名化和派生数据治理的边界。

## 验证证据

- `python -m compileall -q app migrations`：通过。
- 目标 API、SQL 与迁移测试：通过。
- 最新全量验证为 80 passed（真实 MySQL 8.4.11），详见对应任务文件；角色 A 需独立核对。

## 未决事项

`GAP-BE-PRIV-01` 尚未确认，故本任务不实现删除期限、取消窗口和数据处理策略。
