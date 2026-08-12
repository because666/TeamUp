# TeamUp API 契约

> Status: Proposed<br>
> Owner: 角色 B<br>
> Reviewers: 角色 A<br>
> Last Updated: 2026-08-12

## 基础实现状态

FastAPI 基础实现目前已覆盖 `/api/v1` 下的健康检查、微信真实/local 登录、退出、当前用户名片，以及项目创建、详情、更新、发布、关闭和公开列表。

实现返回约定的 `data`/`meta`/`requestId` 信封和结构化错误，并已支持 local/test memory 与 MySQL 8 持久化。`match-v0.1` 纯规则引擎已实现。用户已明确授权按 [ADR-0005](../decisions/ADR-0005-matching-api-data-contract.md) 推荐方案实施首批匹配输入；匹配偏好、成员容量和拉黑基础已在独立堆叠分支实现。上述契约仍为 Proposed，合入 `main` 前必须由角色 A 评审。

### 微信真实登录

`POST /auth/wechat/login` 在服务端配置 `TEAMUP_WECHAT_APP_ID` 和 `TEAMUP_WECHAT_APP_SECRET` 后，会将一次性小程序 `code` 发送到微信 `jscode2session` 接口。服务端按 AppID 命名空间使用返回的 `openid` 做内部用户映射，并签发平台访问凭证；微信身份和 local 测试身份不得共享 subject 命名空间。`session_key` 不进入响应、日志或存储。微信无效 code 返回 `INVALID_LOGIN_CODE`，频率限制返回 `RATE_LIMITED`，外部服务不可用返回 `EXTERNAL_SERVICE_UNAVAILABLE`。配置缺失返回 `WECHAT_NOT_CONFIGURED`，其他微信校验失败返回 `WECHAT_LOGIN_FAILED`，生产或明确关闭替代登录时传入 `local:` code 返回 `LOCAL_LOGIN_DISABLED`。

## 1. 适用范围

本文定义前后端在实现前必须共同遵守的 HTTP 契约基线。正式开发时应由 OpenAPI 文件作为机器可读真值，本文解释跨接口规则和资源边界。

## 2. 通用约定

- 基础路径：`/api/v1`
- 协议：生产环境仅允许 HTTPS
- 内容类型：`application/json; charset=utf-8`
- 时间：ISO 8601 UTC，例如 `2026-08-10T08:00:00Z`
- ID：客户端按不透明字符串处理，不解析数据库含义
- 布尔值和空值使用 JSON 原生类型，不用 `0/1` 或空字符串代替
- 金额若未来引入，使用最小货币单位整数，不使用浮点数
- 客户端不得传 `ownerId` 代替服务端从身份中判断所有权

成功响应：

```json
{
  "data": {},
  "meta": {},
  "requestId": "req_xxx"
}
```

错误响应：

```json
{
  "error": {
    "code": "PROJECT_NOT_EDITABLE",
    "message": "项目当前状态不可编辑",
    "details": []
  },
  "requestId": "req_xxx"
}
```

`message` 用于用户可理解反馈，客户端逻辑只依赖稳定的 `code`，不得解析文案。

## 3. 认证与授权

- `POST /auth/wechat/login` 接收微信一次性登录凭证，返回平台访问凭证。
- 受保护接口使用 `Authorization: Bearer <token>`。
- `401` 表示未认证或会话失效；`403` 表示已认证但无权操作资源。
- 项目、消息、邀请、举报等资源必须做资源级授权。
- 管理接口使用独立角色与审计，不复用普通用户“隐藏按钮”。

## 4. 分页、筛选与排序

列表默认使用游标分页：

```json
{
  "data": [],
  "meta": {
    "nextCursor": "opaque-or-null",
    "hasMore": false
  },
  "requestId": "req_xxx"
}
```

- `limit` 有服务端上限，具体值在性能验证后确认。
- 游标是不透明值；客户端不得修改或依赖其编码。
- 排序字段使用白名单；未知筛选条件返回 `VALIDATION_ERROR`。
- 列表排序必须稳定，必要时用唯一 ID 作为最后排序键。

## 5. 幂等与并发

- 创建邀请、接受邀请、发送消息等可能重复提交的写操作支持 `Idempotency-Key`。
- 更新资源使用 `version` 或等效乐观锁；版本冲突返回 `409 CONFLICT`。
- 接受邀请由服务端事务再次检查项目状态、岗位容量、过期时间和成员唯一性。

## 6. 端点清单

路径和 DTO 在框架确定后进入 OpenAPI；下表定义首版资源面，不允许前后端分别新增同义接口。

| ID | Method | Path | 用途 | PRD |
| --- | --- | --- | --- | --- |
| API-AUTH-01 | POST | `/auth/wechat/login` | 微信登录 | AUTH-001 |
| API-AUTH-02 | POST | `/auth/logout` | 撤销当前会话 | AUTH-002 |
| API-AUTH-03 | POST | `/account/deletion-requests` | 申请注销 | AUTH-002 |
| API-PROF-01 | GET | `/me/profile` | 获取自己的完整名片 | PROF-001 |
| API-PROF-02 | PUT | `/me/profile` | 更新自己的名片 | PROF-001 |
| API-PROF-03 | GET | `/profiles/{profileId}` | 获取允许公开的名片 | PROF-002 |
| API-PROJ-01 | POST | `/projects` | 创建项目草稿 | PROJ-001 |
| API-PROJ-02 | GET | `/projects/{projectId}` | 项目详情 | PROJ-001 |
| API-PROJ-03 | PATCH | `/projects/{projectId}` | 更新自己的项目 | PROJ-001 |
| API-PROJ-04 | POST | `/projects/{projectId}/publish` | 发布项目 | PROJ-001 |
| API-PROJ-05 | POST | `/projects/{projectId}/close` | 关闭项目 | PROJ-001 |
| API-PROJ-MEMBER-01 | GET | `/projects/{projectId}/members` | owner/有效成员读取项目成员 | PROJ-001 / TEAM-001 |
| API-DISC-01 | GET | `/projects` | 项目大厅筛选 | DISC-001 |
| API-DISC-02 | GET | `/profiles` | 人才大厅筛选 | DISC-002 |
| API-MATCH-PREF-01 | GET | `/me/match-preferences` | 获取匹配方向和时间偏好 | MATCH-001/002 |
| API-MATCH-PREF-02 | PUT | `/me/match-preferences` | 更新匹配方向和时间偏好 | MATCH-001/002 |
| API-MATCH-01 | GET | `/projects/{projectId}/matches` | 指定岗位的候选成员 | MATCH-001/002 |
| API-MATCH-02 | GET | `/me/project-matches` | 用户候选项目 | MATCH-001/002 |
| API-MATCH-03 | POST | `/recommendation-impressions` | 登记客户端实际展示的候选与位置 | MATCH-003 |
| API-CONV-01 | POST | `/conversations` | 发起或取得会话 | MSG-001 |
| API-CONV-02 | GET | `/conversations` | 会话列表 | MSG-001 |
| API-MSG-01 | GET | `/conversations/{conversationId}/messages` | 消息分页 | MSG-001 |
| API-MSG-02 | POST | `/conversations/{conversationId}/messages` | 发送文本消息 | MSG-001 |
| API-TEAM-01 | POST | `/invitations` | 创建岗位邀请 | TEAM-001 |
| API-TEAM-02 | POST | `/invitations/{invitationId}/accept` | 接受邀请 | TEAM-001 |
| API-TEAM-03 | POST | `/invitations/{invitationId}/reject` | 拒绝邀请 | TEAM-001 |
| API-SAFE-01 | POST | `/reports` | 提交举报 | SAFE-001 |
| API-SAFE-02 | POST | `/blocks` | 拉黑用户 | SAFE-001 |
| API-SAFE-03 | DELETE | `/blocks/{blockedUserId}` | 取消拉黑 | SAFE-001 |

## 7. 关键 DTO 最小字段

### 匹配输入扩展（Proposed，任务分支已实现）

为避免给现有 `PUT /me/profile` 增加字段后被旧客户端整资源覆盖，方向和时间偏好使用独立资源：

```json
{
  "desiredDirections": ["AI", "后端"],
  "availabilitySlots": [
    {
      "timezone": "Asia/Shanghai",
      "weekday": 6,
      "startMinute": 540,
      "endMinute": 720
    }
  ],
  "version": 1,
  "updatedAt": "2026-08-11T08:00:00Z"
}
```

- `desiredDirections` 为 `0..10` 项，每项为去除首尾空格后的 `1..64` 字符且大小写不敏感去重；受控方向词表仍待角色 A 提供，在此之前后端不从自由文本推断方向；
- `availabilitySlots` 最多 21 项，`weekday` 为 `1..7`，分钟范围为当天 `0..1440`，同一时区/星期不能重叠；P0 只接受 `Asia/Shanghai`，避免未定义的跨时区周期和夏令时语义；
- `PUT /me/match-preferences` 使用 `version` 乐观锁；尚未创建时 `version=0`；
- 尚未创建时 GET 返回 `data: null` 和 `meta.state: INCOMPLETE`；已创建时返回完整 DTO 和 `meta.state: COMPLETE`；PUT 请求不传 `updatedAt`，成功响应返回服务端的新 `version` 和 `updatedAt`；
- 空数组表示用户明确暂不提供，不从简介、专业或定位信息推断；
- 用户关闭名片公开后，该资源仍可编辑，但不会进入新的他人匹配结果。

现有岗位 DTO Proposed 新增（任务分支已实现）：

```json
{
  "skills": ["Python", "MySQL", "Docker"],
  "requiredSkills": ["Python"],
  "requiredAvailabilitySlots": [],
  "collaborationRole": "MEMBER"
}
```

- `skills` 和 `requiredSkills` 每项为 `1..64` 字符、均必须大小写不敏感去重，且 `requiredSkills` 是 `skills` 的子集；历史和新建时省略 required 均为 `[]`；
- 更新既有项目时，旧客户端省略 `requiredSkills` 表示保留原值，并与新的 `skills` 取交集，不能隐式新增 required；
- `requiredAvailabilitySlots` 使用相同时间段 DTO；为空时只比较现有 `hoursPerWeek`，不作时间段硬过滤；
- `collaborationRole` 枚举为 `LEADER | MEMBER | FLEXIBLE`，历史岗位迁移为 `MEMBER`；
- 项目层增加 `collaborationScenarios`；新建省略时为 `[]`，更新省略时保留原值。它与用户名片已有字段应使用同一受控枚举，该词表仍待角色 A 提供。

专业和经历因素在受控专业分类及独立 experience 契约落地前必须保持 missing，不允许用自由文本 `major`、`bio` 或项目说明猜分。

### 项目成员与岗位容量（Proposed，任务分支已实现）

现有岗位响应增加只读字段：

```json
{
  "id": "role_opaque_id",
  "headcount": 2,
  "filledCount": 1,
  "remainingCount": 1
}
```

- `filledCount` 只统计 `ACTIVE` 成员，`remainingCount = headcount - filledCount`；
- 客户端不得提交或修改这两个字段，服务端每次从成员关系计算；
- 项目关闭后成员关系保留，容量字段仍反映已有成员，但不允许新增成员；
- P0 一个用户在同一项目最多属于一个岗位。

`API-PROJ-MEMBER-01`：

```http
GET /api/v1/projects/{projectId}/members
Authorization: Bearer <token>
```

成功响应的 `data` 是成员数组：

```json
[
  {
    "id": "mem_opaque_id",
    "projectId": "prj_opaque_id",
    "roleId": "role_opaque_id",
    "roleName": "后端开发",
    "userId": "usr_opaque_id",
    "status": "ACTIVE",
    "joinedAt": "2026-08-12T08:00:00Z"
  }
]
```

- 仅项目 owner 或该项目 `ACTIVE` 成员可读取；其他已认证用户返回 `403 FORBIDDEN`；
- 不存在或不可见项目返回 `404 RESOURCE_NOT_FOUND`，未认证返回 `401`；
- 响应不包含微信身份、联系方式、非公开名片或内部邀请信息；
- 当前没有公共成员写接口。成员只能由后续 `API-TEAM-02` 接受邀请事务创建，禁止客户端直接添加成员；
- 内部创建必须锁定项目和岗位，重新检查 `PUBLISHED`、岗位 `OPEN`、用户状态、唯一成员与容量；失败使用 `PROJECT_NOT_MATCHABLE`、`ROLE_NOT_OPEN`、`MEMBER_ALREADY_EXISTS` 或 `ROLE_FULL`。

### 用户拉黑（Proposed，任务分支已实现）

`API-SAFE-02`：

```http
POST /api/v1/blocks
Authorization: Bearer <token>
Content-Type: application/json

{"blockedUserId": "usr_opaque_id"}
```

成功时返回当前用户创建的最小关系结果：

```json
{
  "blockedUserId": "usr_opaque_id",
  "createdAt": "2026-08-12T08:00:00Z"
}
```

- `blockedUserId` 必须是存在且状态有效的用户，不允许等于当前用户；
- 重复提交同一方向关系幂等返回原始 `createdAt`，不创建第二条记录；
- 自己拉黑返回 `422 CANNOT_BLOCK_SELF`，目标不存在或不可见返回 `404 RESOURCE_NOT_FOUND`；
- 响应不包含原因，也不说明目标是否已反向拉黑当前用户。

`API-SAFE-03`：

```http
DELETE /api/v1/blocks/{blockedUserId}
Authorization: Bearer <token>
```

响应为 `{"blockedUserId":"usr_opaque_id","removed":true}`；关系不存在时仍返回 `200` 和 `removed=false`。取消拉黑只删除当前用户创建的单向关系，不删除对方创建的关系，也不恢复历史邀请、消息或成员关系。

服务端内部双向检查只要存在 `(A,B)` 或 `(B,A)` 任一关系就视为已阻断。当前分支已将该检查接入新成员创建；消息、邀请、发现和匹配模块实现时必须复用同一检查，不能根据客户端状态判断。

### ProjectSummary

```json
{
  "id": "project_id",
  "title": "项目标题",
  "direction": "AI",
  "stage": "DEVELOPMENT",
  "status": "PUBLISHED",
  "requiredSkills": ["Python"],
  "openRoleCount": 2,
  "publishedAt": "2026-08-10T08:00:00Z"
}
```

### MatchResult

> 以下扩展字段和列表信封属于 ADR-0005 Proposed，角色 A 评审前不得视为已发布接口。

```json
{
  "targetType": "PROJECT_ROLE",
  "targetId": "role_opaque_id",
  "targetSummary": {
    "projectId": "project_opaque_id",
    "projectTitle": "校园创新项目",
    "roleId": "role_opaque_id",
    "roleName": "后端开发",
    "direction": "AI",
    "skillLabels": ["Python", "MySQL"]
  },
  "score": 82,
  "confidence": 0.9,
  "informationSufficient": true,
  "engineType": "RULE",
  "engineVersion": "match-v0.1",
  "modelVersion": null,
  "factors": [
    {"key": "skill", "score": 90, "reasonCode": "SKILL_OVERLAP_HIGH"}
  ],
  "missingInformation": []
}
```

`targetType` Proposed 枚举为 `PROFILE | PROJECT_ROLE`：

- `API-MATCH-01` 返回 `PROFILE`，`targetId` 是候选用户的 opaque ID；`targetSummary` 只含公开昵称和公开技能标签。
- `API-MATCH-02` 返回 `PROJECT_ROLE`，`targetId` 是岗位 ID；`targetSummary` 包含跳转项目详情和展示岗位所需的最小公开字段。

`engineType` 可为 `RULE` 或 `ML_RANKER`。自然语言解释可以由客户端模板或生成式 AI 生成，但 `score`、`confidence`、`informationSufficient`、`engineVersion`、`modelVersion` 和 `factors` 只能来自匹配服务。内部 `rankingScore` 只用于排序，不返回客户端。

### 匹配列表请求与响应（Proposed）

`API-MATCH-01`：

```http
GET /api/v1/projects/{projectId}/matches?roleId={roleId}&limit=20&cursor={opaqueCursor}
Authorization: Bearer <token>
```

- 仅项目 owner 可调用；`roleId` 必须属于路径中的项目；
- 以该岗位为上下文返回 `PROFILE` 目标；
- 非 owner 返回 `403 FORBIDDEN`，不存在或不可见的项目/岗位返回 `404 RESOURCE_NOT_FOUND`；
- 项目或岗位不是可匹配状态时返回 `409 PROJECT_NOT_MATCHABLE`。

`API-MATCH-02`：

```http
GET /api/v1/me/project-matches?limit=20&cursor={opaqueCursor}
Authorization: Bearer <token>
```

- 只使用当前登录用户的完整名片；该结果仅返回本人，因此不要求名片已公开；
- 按具体开放岗位返回 `PROJECT_ROLE` 目标，同一项目可以因不同岗位出现多条结果；
- 名片不存在或未完成时返回 `409 MATCH_PROFILE_INCOMPLETE`；关闭公开只阻止该用户进入 `API-MATCH-01`，不阻止本人使用 `API-MATCH-02`。

两个接口均使用统一 envelope：

```json
{
  "data": [],
  "meta": {
    "recommendationRequestId": "rrq_opaque_random_id",
    "nextCursor": null,
    "hasMore": false
  },
  "requestId": "req_trace_id"
}
```

- 首次请求不传 `cursor`；`limit` 默认 20，最大 50；
- `cursor` 只能由上一页 `meta.nextCursor` 原样传回，并绑定请求者、方向、上下文和候选快照；
- 同一推荐请求复用相同 `recommendationRequestId` 和冻结排序；读取每页时仍重新检查状态、拉黑、容量和公开权限，失效目标静默跳过；
- 跳过失效目标后继续向后扫描直到填满 `limit` 或快照耗尽；`nextCursor` 指向最后实际扫描 rank，避免下一页重复；
- 非法、跨用户或跨上下文 cursor 返回 `422 INVALID_CURSOR`；过期 cursor 返回 `410 RECOMMENDATION_EXPIRED`；
- 无候选是 `200` 和空 `data`，不是服务异常；
- 最大候选窗口建议 200、快照建议有效 24 小时，均保持 Proposed，需产品和负载评审。

### RecommendationImpressionRequest

```json
{
  "recommendationRequestId": "rec_request_id",
  "items": [
    {"targetType": "PROJECT_ROLE", "targetId": "opaque_id", "position": 1}
  ],
  "occurredAt": "2026-08-10T08:00:00Z"
}
```

服务端只能接受先前在该用户推荐响应中签发的 `recommendationRequestId`、目标类型和候选，执行幂等去重并限制时间窗口。曝光写入前再次检查推荐请求所有者和目标资格；已关闭、被拉黑或已满员目标不再登记新曝光。建议规则：

- `items` 为实际进入可视区域的子集，数量 `1..50`，`position` 从 1 开始且不能重复；
- 唯一键为推荐请求、viewer、target type 和 target ID；
- 重复提交同一 position 返回原结果，不产生第二条曝光；同一目标改报不同 position 返回 `409 IMPRESSION_CONFLICT`；
- 不属于候选快照返回 `422 INVALID_RECOMMENDATION_TARGET`；请求过期返回 `410 RECOMMENDATION_EXPIRED`；
- `occurredAt` 仅作客户端观察时间，服务端另存接收时间并限制可接受时钟偏差。

详情、沟通、邀请和组队结果由对应业务接口在服务端关联记录，不接受客户端直接声明“成功组队”。

## 8. 兼容性规则

- 新增可选响应字段通常向后兼容；删除、重命名、改类型或改变含义属于破坏性变更。
- 破坏性变更必须更新版本、OpenAPI、前后端任务和 ADR/迁移说明。
- 客户端应忽略未知响应字段，但不得忽略未知枚举导致错误状态被当作成功。
- API 实现完成后，契约测试必须验证 OpenAPI 与实际响应一致。
