# TUP-20260811-match-api-data-contract 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/docs/TUP-20260811-match-api-data-contract`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-11

## 1. 评审范围

- [ADR-0005](../../decisions/ADR-0005-matching-api-data-contract.md)
- [API 契约](../../architecture/API_CONTRACT.md) 的匹配输入扩展、MatchResult、列表分页和曝光请求；
- [数据模型](../../architecture/DATA_MODEL.md) 的匹配接入数据扩展；
- 现有前端项目/名片 DTO 的兼容与升级顺序。

## 2. 需要角色 A 明确确认

| ID | 决策项 | 推荐方案 | 角色 A 结论 |
| --- | --- | --- | --- |
| MA-001 | 用户找项目的目标粒度 | 每个结果对应具体 `PROJECT_ROLE`，同一项目可出现多个岗位 | TBD |
| MA-002 | 项目方找成员的入口 | 路径保持项目级，必须传属于该项目的 `roleId` | TBD |
| MA-003 | 自己名片关闭公开后的行为 | 本人仍可找项目，但不进入项目方候选 | TBD |
| MA-004 | 方向与时间偏好 | 独立 `/me/match-preferences`，不扩展旧 profile PUT | TBD |
| MA-005 | 岗位 required skill | `requiredSkills` 是 `skills` 子集；历史技能全部为 bonus | TBD |
| MA-006 | 时间段输入 | 星期、开始/结束分钟；P0 固定 `Asia/Shanghai`；空集合表示无硬时间段 | TBD |
| MA-007 | 合作身份 | 岗位增加 `LEADER/MEMBER/FLEXIBLE`，历史为 `MEMBER` | TBD |
| MA-008 | 列表展示摘要 | 返回公开昵称/技能或项目/岗位最小摘要，不额外请求 N 次详情 | TBD |
| MA-009 | 分页稳定性 | 保存有时限的候选快照，翻页实时再检查硬约束 | TBD |
| MA-010 | 推荐窗口 | 建议 24 小时、候选窗口 200、默认页 20、最大 50 | TBD |
| MA-011 | 信息不足展示 | 使用 `informationSufficient` 和 `missingInformation`，不解释为能力不足 | TBD |
| MA-012 | 经历与专业因素 | 独立后续契约落地前保持 missing，不从自由文本猜分 | TBD |
| MA-013 | 受控词表 | 角色 A 提供技能别名、方向和协作场景的首版值及展示名 | TBD |

## 3. 前端验收关注点

- 页面可以用 `targetType` 区分候选成员和候选岗位；
- `targetSummary` 足够渲染列表，但不包含联系方式、非公开经历或治理原因；
- `nextCursor` 原样回传，不解析或自行排序；
- 空列表显示正常无结果状态，不显示系统错误；
- `MATCH_PROFILE_INCOMPLETE`、`PROJECT_NOT_MATCHABLE`、`RECOMMENDATION_EXPIRED` 和 `IMPRESSION_CONFLICT` 有明确交互；
- 前端只登记实际展示的候选，不上报“成功组队”等服务端结果。

## 4. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| Finding ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |

只有 MA-001..013 均填写结论且 Overall Decision 为 Approved，ADR-0005 才能改为 Accepted 并进入实现任务。
