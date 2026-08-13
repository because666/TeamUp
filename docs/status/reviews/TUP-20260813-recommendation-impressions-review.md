# TUP-20260813-recommendation-impressions 评审记录

> Status: Proposed  
> Reviewer: 角色 A  
> Review Target: `role-b/feature/TUP-20260813-recommendation-impressions`  
> Last Updated: 2026-08-13

## 待评审范围

- `POST /api/v1/recommendation-impressions` 的请求归属、候选归属和实时可见性校验。
- 重复曝光幂等与位置冲突语义。
- `recommendation_requests`、`recommendation_candidates`、`recommendation_impressions` 迁移及保留周期。
- 当前推荐 cursor 仍为进程内快照，是否接受该阶段性限制。

## 负责人验证证据

- 最新全量验证为 80 passed（真实 MySQL 8.4.11），详见对应任务文件；角色 A 需独立核对。
- `python -m compileall -q services/api/app services/api/migrations`：通过。
- `git diff --check`：通过。

## 未决事项

隐私/模型数据政策尚未确认曝光保留周期；ADR-0005 的完整持久化推荐快照和 Outcome 事件仍未实施。
