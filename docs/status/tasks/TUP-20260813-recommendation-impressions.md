# TUP-20260813-recommendation-impressions

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Branch: `role-b/feature/TUP-20260813-recommendation-impressions`  
> Last Updated: 2026-08-13

## 目标

为已返回的推荐结果增加最小化曝光登记接口，记录客户端实际看到的候选，用于后续可解释分析与 P0 事件链积累。

## 范围

- 保存推荐请求及候选的最小快照索引。
- 提供 `POST /api/v1/recommendation-impressions`，校验请求归属、候选归属、过期时间和客户端时间窗口。
- 同一请求、用户和候选重复上报幂等；同一候选以不同位置上报返回冲突。
- MemoryStore 与 SQLAlchemyStore 保持同一错误码和权限语义，并增加迁移与测试。

## 非目标

- 不实现模型训练、权重调整、Outcome 事件或个性化策略变更。
- 不把当前进程内匹配 cursor 改造成可跨进程恢复的推荐分页；该架构仍受 Proposed ADR-0005 约束。
- 不记录消息正文、私密资料或原始敏感特征。

## 基线与影响

- 基线提交：`43dc95e`
- 接口：新增曝光登记接口；匹配响应中的 `recommendationRequestId` 作为 opaque 请求标识。
- 数据：新增 `recommendation_requests`、`recommendation_candidates`、`recommendation_impressions` 表及向前迁移。
- 安全：仅允许请求所属 viewer 上报；候选必须来自该请求快照；时间戳限制为服务端当前时间前 24 小时至后 5 分钟。

## 验证

- `python -m pytest -ra`（MySQL 8.4.11）：80 passed。
- `python -m alembic upgrade head / downgrade base / upgrade head`：迁移往返通过，最终为 `20260813_0010 (head)`。
- `python -m compileall -q app tests migrations` 与 `git diff --check`：通过。
- 已覆盖 Memory/SQL 的归属校验、目标实时可见性、重复幂等、位置冲突、无效候选和迁移完整性；真实 MySQL 验证发现并修复推荐请求父记录必须先于候选 flush 的外键顺序问题。

## 剩余风险

- 推荐分页 cursor 仍是进程内快照，服务重启后不可恢复；数据库目前保存请求/候选索引以支撑曝光归属，不保存完整评分 DTO。
- 曝光保留周期、后续 Outcome 事件和训练数据治理仍待隐私政策与 ADR-0005 评审。
