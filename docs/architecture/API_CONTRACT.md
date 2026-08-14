# TeamUp API 契约

> Status: Proposed<br>
> Owner: 角色 B<br>
> Reviewers: 角色 A<br>
> Last Updated: 2026-08-12

## 基础实现状态

FastAPI 基础实现目前已覆盖 `/api/v1` 下的健康检查、微信真实/local 登录、退出、当前用户名片和公开名片发现，以及项目创建、详情、更新、发布、关闭、公开筛选列表和当前用户项目列表。

实现返回约定的 `data`/`meta`/`requestId` 信封和结构化错误，并已支持 local/test memory 与 MySQL 8 持久化。`match-v0.1` 纯规则引擎及其岗位级 `API-MATCH-01/02` 适配已在任务分支实现。用户已明确授权按 [ADR-0005](../decisions/ADR-0005-matching-api-data-contract.md) 推荐方案实施首批匹配输入；匹配偏好、成员容量和拉黑基础已在独立堆叠分支实现。上述契约仍为 Proposed，合入 `main` 前必须由角色 A 评审。

### 微信真实登录

`POST /auth/wechat/login` 在服务端配置 `TEAMUP_WECHAT_APP_ID` 和 `TEAMUP_WECHAT_APP_SECRET` 后，会将一次性小程序 `code` 发送到微信 `jscode2session` 接口。服务端按 AppID 命名空间使用返回的 `openid` 做内部用户映射，并签发平台访问凭证；微信身份和 local 测试身份不得共享 subject 命名空间。`session_key` 不进入响应、日志或存储。微信无效 code 返回 `INVALID_LOGIN_CODE`，频率限制返回 `RATE_LIMITED`，外部服务不可用返回 `EXTERNAL_SERVICE_UNAVAILABLE`。配置缺失返回 `WECHAT_NOT_CONFIGURED`，其他微信校验失败返回 `WECHAT_LOGIN_FAILED`，生产或明确关闭替代登录时传入 `local:` code 返回 `LOCAL_LOGIN_DISABLED`。

命中服务端限流时使用 HTTP `429`，错误码为 `RATE_LIMITED`，并通过 `Retry-After` 响应头返回建议等待秒数。

### 发现与公开名片（Proposed，任务分支实现）

`API-DISC-01`：

```http
GET /api/v1/projects?status=PUBLISHED&direction=AI&competition=互联网%2B&stage=IDEA&skill=Python&limit=20&cursor=<opaque>
Authorization: Bearer <token>
```

仅返回 `PUBLISHED` 项目。`direction`、`competition`、`stage` 和 `skill` 均为可选精确筛选，结果按最新发布时间和项目 ID 稳定倒序分页；`status` 当前固定为 `PUBLISHED`，关闭项目不进入项目大厅。

`API-DISC-02`：

```http
GET /api/v1/profiles?skill=Python&direction=AI&collaborationRole=FLEXIBLE&minHoursPerWeek=6&maxHoursPerWeek=10&limit=20&cursor=<opaque>
Authorization: Bearer <token>
```

仅返回账号 `ACTIVE`、名片明确 `visibility=true` 的用户。`direction` 匹配用户独立 `match-preferences.desiredDirections`，不从专业、简介或协作场景推断；`skill`、合作角色和投入时间为可选筛选。响应只包含公开名片字段和不可变 `id`，不包含 `version`。

`GET /api/v1/profiles/{profileId}` 返回同一公开名片 DTO。当前用户、未公开、非活跃账号或双方任一方向拉黑均返回 `404 RESOURCE_NOT_FOUND`，避免泄露资源存在性。

`GET /api/v1/me/projects?status=DRAFT|PUBLISHED|CLOSED&limit=20&cursor=<opaque>` 只返回当前用户拥有的项目，按更新时间和项目 ID 稳定倒序分页；省略 `status` 时返回该用户全部项目。

本切片要求先认证；Guest 是否可浏览公开摘要仍由 `IA-GAP-01` 决定，未确认前不开放匿名访问。

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

- 创建邀请和接受邀请当前使用领域唯一键与状态机提供重复保护；通用 `Idempotency-Key` 持久化仍为 `Proposed`，后续消息等不能据此假定已实现。
- 发送消息使用请求体 `clientMessageId` 作为 sender 范围的领域幂等键；同 key 同正文返回原消息，不同正文返回 `409 MESSAGE_IDEMPOTENCY_CONFLICT`。
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
| API-PROJ-03-WX | PUT | `/projects/{projectId}` | 微信客户端兼容的等价项目更新 | PROJ-001 |
| API-PROJ-04 | POST | `/projects/{projectId}/publish` | 发布项目 | PROJ-001 |
| API-PROJ-05 | POST | `/projects/{projectId}/close` | 关闭项目 | PROJ-001 |
| API-PROJ-06 | GET | `/me/projects` | 当前用户项目列表 | GAP-PROJ-03 |
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

### 双人会话与文本消息（Proposed，任务分支已实现）

`API-CONV-01`：

```http
POST /api/v1/conversations
Authorization: Bearer <token>
Content-Type: application/json

{"projectId":"prj_opaque_id","otherUserId":"usr_opaque_id"}
```

成功 `data`：

```json
{
  "id": "con_opaque_id",
  "projectId": "prj_opaque_id",
  "participantUserIds": ["usr_a", "usr_b"],
  "lastMessageAt": null,
  "createdAt": "2026-08-12T10:00:00Z"
}
```

- 项目必须为 `PUBLISHED`，other user 必须是另一名有效用户；
- 两名参与者中至少一人必须是项目 owner 或 `ACTIVE` 成员，支持 owner 联系人才和候选人联系项目方；
- 同一项目与同一对用户重复创建返回原会话，不产生第二条记录；
- 任一方向拉黑返回 `409 USER_BLOCKED`；自己建会话返回 `422 CANNOT_MESSAGE_SELF`；
- 无效/不可联系项目或用户返回 `404 RESOURCE_NOT_FOUND`，与项目无关的两名用户返回 `403 FORBIDDEN`。

`API-CONV-02`：

```http
GET /api/v1/conversations?limit=20&cursor=<opaque>
Authorization: Bearer <token>
```

只返回当前用户作为 `ACTIVE` 参与者的会话摘要，不包含消息正文。按 `lastMessageAt ?? createdAt`、`id` 倒序；`limit` 默认 20、最大 50。响应 `meta` 为 `nextCursor` 和 `hasMore`。

`API-MSG-01`：

```http
GET /api/v1/conversations/{conversationId}/messages?limit=20&cursor=<opaque>
Authorization: Bearer <token>
```

只允许参与者读取；其他用户与不存在会话统一返回 `404 RESOURCE_NOT_FOUND`。消息按 `(createdAt, id)` 正序稳定分页，`limit` 默认 20、最大 50。拉黑不删除或隐藏双方作为原参与者可读取的历史消息。

`API-MSG-02`：

```http
POST /api/v1/conversations/{conversationId}/messages
Authorization: Bearer <token>
Content-Type: application/json

{"clientMessageId":"mobile-20260812-001","content":"你好，想了解项目"}
```

成功 `data`：

```json
{
  "id": "msg_opaque_id",
  "conversationId": "con_opaque_id",
  "senderUserId": "usr_sender",
  "clientMessageId": "mobile-20260812-001",
  "type": "TEXT",
  "content": "你好，想了解项目",
  "status": "SENT",
  "createdAt": "2026-08-12T10:05:00Z"
}
```

- `clientMessageId` 长度 1..64，只允许字母、数字、点、下划线、冒号和连字符；同一 sender 全局唯一；
- `content` 去除首尾空白后长度为 1..1000，仅作为纯文本保存；
- 同 sender、同 key、同会话且同正文的重试返回原消息；key 已用于其他会话或正文时返回 `409 MESSAGE_IDEMPOTENCY_CONFLICT`；
- 已成功消息的相同重试优先返回原结果；任一方向拉黑只阻止真正的新消息并返回 `409 USER_BLOCKED`；
- 服务端不记录消息正文到应用日志；已读、撤回、附件、推送和实时 WebSocket 不在当前接口范围。

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

### 项目岗位邀请（Proposed，任务分支已实现）

`API-TEAM-01`：

```http
POST /api/v1/invitations
Authorization: Bearer <token>
Content-Type: application/json

{
  "projectId": "prj_opaque_id",
  "roleId": "role_opaque_id",
  "inviteeUserId": "usr_opaque_id"
}
```

成功返回：

```json
{
  "id": "inv_opaque_id",
  "projectId": "prj_opaque_id",
  "roleId": "role_opaque_id",
  "inviterUserId": "usr_owner_id",
  "inviteeUserId": "usr_invitee_id",
  "status": "PENDING",
  "expiresAt": "2026-08-19T08:00:00Z",
  "createdAt": "2026-08-12T08:00:00Z",
  "respondedAt": null
}
```

- 只有项目 owner 可创建；项目必须为 `PUBLISHED`，岗位必须为 `OPEN` 且有剩余容量；
- invitee 必须是另一名有效用户，且不是项目现有成员；任一方向拉黑均返回 `409 USER_BLOCKED`；
- 首版有效期固定为服务端创建后 7 天，该时长由角色 A 评审；客户端不提交或延长过期时间；
- 同一项目、岗位和 invitee 最多一条有效 `PENDING` 邀请；重复创建返回原 `id`、`createdAt` 和 `expiresAt`；
- 自邀返回 `422 CANNOT_INVITE_SELF`；其他失败使用 `FORBIDDEN`、`PROJECT_NOT_MATCHABLE`、`ROLE_NOT_OPEN`、`ROLE_FULL`、`MEMBER_ALREADY_EXISTS` 或 `RESOURCE_NOT_FOUND`。

`API-TEAM-02`：

```http
POST /api/v1/invitations/{invitationId}/accept
Authorization: Bearer <token>
```

只有 invitee 可操作；其他用户统一收到 `404 RESOURCE_NOT_FOUND`。成功响应的 `data` 为：

```json
{
  "invitation": {"id": "inv_opaque_id", "status": "ACCEPTED"},
  "member": {
    "id": "mem_opaque_id",
    "projectId": "prj_opaque_id",
    "roleId": "role_opaque_id",
    "roleName": "后端开发",
    "userId": "usr_invitee_id",
    "status": "ACTIVE",
    "joinedAt": "2026-08-12T08:05:00Z"
  }
}
```

实际邀请对象包含与创建响应相同的完整字段。接受事务按固定锁顺序重新检查邀请、用户、双向拉黑、项目、岗位、容量和成员唯一性；并发接受不能超额。本人重复接受已 `ACCEPTED` 邀请返回原确定结果，不创建第二个成员。已拒绝、过期、取消或其他不可接受状态返回 `409 INVITATION_NOT_ACTIONABLE`。

`API-TEAM-03`：

```http
POST /api/v1/invitations/{invitationId}/reject
Authorization: Bearer <token>
```

只有 invitee 可拒绝自己的 `PENDING` 邀请。成功返回状态为 `REJECTED` 的完整邀请；重复拒绝幂等返回原结果。已接受、过期或取消的邀请返回 `409 INVITATION_NOT_ACTIONABLE`。拒绝不创建成员，也不记录拒绝原因。

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

服务端内部双向检查只要存在 `(A,B)` 或 `(B,A)` 任一关系就视为已阻断。当前堆叠分支已将该检查接入新成员创建、邀请创建/接受以及新会话/新消息；发现和匹配模块实现时必须复用同一检查，不能根据客户端状态判断。

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

当前任务分支的实现说明：`API-MATCH-01/02` 使用 `RULE/match-v0.1` 返回上述 DTO。`recommendationRequestId` 和 cursor 的分页快照仍由服务端进程内保存、默认有效 24 小时，服务重启后 cursor 失效；首次生成推荐时会将请求和候选索引写入 `recommendation_requests`/`recommendation_candidates`，用于曝光归属校验。`API-MATCH-03` 将曝光事件持久化到 `recommendation_impressions`，但不改变当前进程内分页架构，也不代表 ADR-0005 的完整持久化快照方案已 Accepted。

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

`API-MATCH-03` 的服务端时间窗口为当前时间前 24 小时至后 5 分钟；无时区时间戳、越界时间戳和跨用户请求均拒绝。请求、候选与曝光表已提供向前迁移，保留周期仍由隐私/模型数据政策决定。

详情、沟通、邀请和组队结果由对应业务接口在服务端关联记录，不接受客户端直接声明“成功组队”。

### 举报提交（Proposed，任务分支已实现）

`POST /api/v1/reports` 接受 `targetType`（`USER|PROJECT|MESSAGE`）、`targetId`、受控 `reason`（`SPAM|HARASSMENT|FRAUD|INAPPROPRIATE_CONTENT|OTHER`）和可选 `description`。服务端从 bearer 会话确定 reporter。自己、不可见用户/项目以及 reporter 无权访问的会话消息统一返回 `404 RESOURCE_NOT_FOUND`；用户也不能举报自己发送的消息。初始状态为 `PENDING`，同一 reporter、目标和原因的待处理举报幂等返回原记录。管理员审核、下架、申诉和审计接口不在本切片范围。

### 注销申请（Proposed，任务分支已实现）

`POST /api/v1/account/deletion-requests` 仅使用当前 bearer 会话确定用户，不接收客户端用户 ID。首次成功创建 `PENDING` 申请后，账号进入 `DELETION_PENDING` 并立即撤销该用户全部平台会话；该账号不能重新登录或访问受保护接口。并发或重复申请返回同一待处理申请。该接口不直接物理删除或匿名化数据；等待期、取消申请、最终处理和各类数据保留策略仍由 `GAP-BE-PRIV-01` 决定。

## 8. 兼容性规则

- 新增可选响应字段通常向后兼容；删除、重命名、改类型或改变含义属于破坏性变更。
- 破坏性变更必须更新版本、OpenAPI、前后端任务和 ADR/迁移说明。
- 客户端应忽略未知响应字段，但不得忽略未知枚举导致错误状态被当作成功。
- API 实现完成后，契约测试必须验证 OpenAPI 与实际响应一致。
