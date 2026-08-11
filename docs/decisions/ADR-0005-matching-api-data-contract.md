# ADR-0005: 匹配 API 与数据契约

> Status: Proposed<br>
> Decision Owner: 角色 A（产品契约）/ 角色 B（技术与数据）<br>
> Reviewers: 角色 A / 角色 B<br>
> Date: 2026-08-11

## Context

`match-v0.1` 规则引擎已经实现纯计算，但当前物理数据只有无类型岗位技能、用户每周投入小时和项目方向。required skill、用户方向偏好、时间段、经历、成员容量、拉黑和推荐请求快照尚未落地。现有 API 清单只给出路径与 `MatchResult` 最小字段，没有确定岗位粒度、列表信封、分页、目标摘要或曝光窗口。

若直接实现，会迫使后端自行猜测产品字段，并可能把历史 `skills` 静默当成硬门槛、产生不稳定翻页，或让客户端伪造曝光候选。

## Decision Drivers

- 两个方向都应在岗位粒度使用同一规则语义；
- 保持现有名片、项目和岗位请求向后兼容；
- 相同推荐请求翻页稳定且可追溯到引擎版本；
- 关闭、拉黑、容量和可见性变化必须立即阻止后续暴露或联系；
- 曝光只能引用服务端确实返回过的候选；
- 前端一次请求即可获得列表展示需要的最小公开摘要；
- 不从自由文本或敏感数据推断结构化匹配特征。

## Options

### Option A：每页重新实时计算并使用 keyset cursor

- 优点：不保存候选快照，数据永远最新；
- 缺点：资料或项目变化会导致跨页重复、遗漏和排序漂移；
- 风险：难以准确关联曝光分母与当时的引擎结果。

### Option B：服务端保存有时限的候选快照（推荐）

- 优点：翻页稳定，可验证曝光候选、位置和规则版本；
- 缺点：增加请求/候选表和过期清理；
- 风险：快照生成后资源状态可能变化，因此每页读取和曝光写入仍须重新检查硬约束。

### Option C：客户端接收全部候选并自行分页

- 优点：后端实现简单；
- 缺点：响应过大，泄露不必要候选，无法限制抓取；
- 风险：客户端可以篡改排名和曝光位置。

## Recommended Option

推荐采用 Option B，并按以下契约实施：

1. 匹配目标统一到岗位级：用户找项目时 `targetId` 是 `projectRoleId`；项目方找成员时 `targetId` 是公开名片对应的 `userId`，请求必须指定 `roleId`。
2. 首次查询计算一个有上限的有序候选窗口，保存 `recommendation_requests` 和 `recommendation_candidates`；返回不可猜测的 `recommendationRequestId`。
3. `nextCursor` 是仅服务端可解释的 opaque token，绑定请求者、推荐请求和下一位置；客户端不得构造分数或 offset。
4. 后续翻页复用候选快照以保持顺序，但返回前再次检查账号、公开状态、项目/岗位状态、拉黑、容量和 required skill。失效候选静默跳过，不泄露治理原因。
5. 响应继续使用统一 envelope：`data` 是 `MatchResult[]`，分页和 `recommendationRequestId` 位于 `meta`。
6. 现有岗位 `skills` 保持为全部目标技能；新增 `requiredSkills`，且必须是 `skills` 的子集。历史 `skills` 在迁移后全部视为 bonus，不得自动变为 required。
7. 名片新增结构化 `desiredDirections` 和 `availabilitySlots`；经历通过独立 `experiences` 资源维护。字段未填写时对应因素缺失，不按零分处理。
8. 推荐请求建议有效 24 小时，最大候选窗口建议 200，默认页大小 20、最大 50；这些数值保持 Proposed，由角色 A 评审用户流程、角色 B 在负载验证后共同确认。
9. 曝光唯一键为 `(recommendation_request_id, viewer_user_id, target_type, target_id)`；重复同一位置幂等成功，不同位置冲突。
10. P0 不根据简介、学校层级、微信身份、联系方式、举报或拉黑原因生成匹配特征。

## Decision

`TBD`。当前推荐 Option B；只有角色 A、角色 B 完成 Approval Required 后，才将 ADR 状态改为 `Accepted` 并授权实现。

## Data Migration Strategy

1. 先新增 nullable/空集合兼容字段和新表，不改变现有读写；
2. 将现有 `project_role_skills` 记录标记为 `required = false`；
3. 前后端支持新字段后，再允许项目方显式选择 required；
4. 新匹配端点只在拉黑、成员容量和公开读取边界具备后启用；
5. 删除或重命名旧字段必须另走版本化兼容任务，本 ADR 不授权破坏性迁移。

## Consequences

- 需要新增推荐请求、候选、曝光、方向偏好、时间段、经历、成员和拉黑相关 schema；
- API 响应比最小 `MatchResult` 多一个受控目标摘要，但不包含联系方式和非公开资料；
- 快照需要 TTL 清理和最大候选窗口，避免无限增长；
- 每页/曝光重新检查硬约束会增加查询，但避免使用过期权限结果；
- 角色 A 未批准前，只能作为设计提案，禁止据此发布接口或迁移。

## Approval Required

- 角色 A：岗位级交互、目标摘要、方向/时间/经历字段、24 小时窗口和前端错误处理；
- 角色 B：索引、事务、快照上限、opaque cursor、安全过滤和迁移可回滚性。
