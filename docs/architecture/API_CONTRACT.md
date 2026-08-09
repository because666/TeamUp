# TeamUp API 契约

> Status: Proposed<br>
> Owner: 角色 B<br>
> Reviewers: 角色 A<br>
> Last Updated: 2026-08-10

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
| API-DISC-01 | GET | `/projects` | 项目大厅筛选 | DISC-001 |
| API-DISC-02 | GET | `/profiles` | 人才大厅筛选 | DISC-002 |
| API-MATCH-01 | GET | `/projects/{projectId}/matches` | 岗位候选成员 | MATCH-001/002 |
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

```json
{
  "targetId": "opaque_id",
  "score": 82,
  "confidence": 0.9,
  "engineType": "RULE",
  "engineVersion": "match-v0.1",
  "modelVersion": null,
  "factors": [
    {"key": "skill", "score": 90, "reasonCode": "SKILL_OVERLAP_HIGH"}
  ],
  "missingInformation": []
}
```

`engineType` 可为 `RULE` 或 `ML_RANKER`。自然语言解释可以由客户端模板或生成式 AI 生成，但 `score`、`confidence`、`engineVersion`、`modelVersion` 和 `factors` 只能来自匹配服务。

### RecommendationImpressionRequest

```json
{
  "recommendationRequestId": "rec_request_id",
  "items": [
    {"targetId": "opaque_id", "position": 1}
  ],
  "occurredAt": "2026-08-10T08:00:00Z"
}
```

服务端只能接受先前在该用户推荐响应中签发的 `recommendationRequestId` 和候选，执行幂等去重并限制时间窗口。详情、沟通、邀请和组队结果由对应业务接口在服务端关联记录，不接受客户端直接声明“成功组队”。

## 8. 兼容性规则

- 新增可选响应字段通常向后兼容；删除、重命名、改类型或改变含义属于破坏性变更。
- 破坏性变更必须更新版本、OpenAPI、前后端任务和 ADR/迁移说明。
- 客户端应忽略未知响应字段，但不得忽略未知枚举导致错误状态被当作成功。
- API 实现完成后，契约测试必须验证 OpenAPI 与实际响应一致。
