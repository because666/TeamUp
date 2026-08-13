# TeamUp 核心数据模型

> Status: Proposed<br>
> Owner: 角色 B<br>
> Reviewers: 角色 A<br>
> Last Updated: 2026-08-12

## 基础实现状态

首个 FastAPI 切片保留 local/test 内存适配器，并按 [ADR-0004](../decisions/ADR-0004-mysql-data-access.md) 实现了 MySQL 8 持久化适配器。匹配偏好、项目成员、用户拉黑、岗位邀请及会话消息分别通过第二至第六版堆叠迁移实现。合入 `main` 仍需角色 A 评审。

首批已实现物理表：

| 表 | 用途 | 关键约束 |
| --- | --- | --- |
| `users` | 内部用户与微信 subject | subject 唯一、状态检查 |
| `sessions` | 平台会话 | 只存 SHA-256 token 摘要、过期与撤销时间、用户外键 |
| `profiles` | 当前能力名片 | 用户主键/外键、版本与枚举检查 |
| `profile_skills` | 有序名片技能 | `(user_id, position)` 主键 |
| `profile_collaboration_scenarios` | 有序协作场景 | `(user_id, position)` 主键 |
| `projects` | 项目主体 | owner 外键、状态/版本检查、列表索引 |
| `project_roles` | 招募岗位 | 项目外键、岗位位置唯一、人数/时间/状态检查 |
| `project_role_skills` | 有序岗位技能 | `(role_id, position)` 主键 |
| `match_preferences` | 当前用户匹配偏好 | 用户主键/外键、独立版本检查 |
| `match_preference_directions` | 有序方向偏好 | `(user_id, position)` 主键、用户/方向唯一 |
| `match_preference_availability_slots` | 有序用户可用时间段 | `(user_id, position)` 主键、范围检查 |
| `project_collaboration_scenarios` | 有序项目协作场景 | `(project_id, position)` 主键、项目/场景唯一 |
| `project_role_availability_slots` | 有序岗位必需时间段 | `(role_id, position)` 主键、范围检查 |
| `project_members` | 项目有效成员 | 项目/用户唯一、项目/岗位复合外键、状态检查和容量索引 |
| `blocks` | 用户单向拉黑关系 | `(blocker_id, blocked_id)` 主键、禁止自己拉黑和反向查询索引 |
| `invitations` | 项目岗位邀请与状态机 | 项目/岗位复合外键、待处理唯一键、用户外键、状态/自邀检查和查询索引 |
| `conversations` | 双人项目会话 | 项目外键、项目/参与者排序组合唯一键、最近消息时间索引 |
| `conversation_participants` | 会话有效参与者 | `(conversation_id, user_id)` 主键、用户/状态查询索引 |
| `messages` | 纯文本站内消息 | 发送者/参与者复合外键、sender/client ID 唯一、稳定分页索引和状态检查 |

数据库时间以 UTC 秒精度写入，API 输出恢复为带 UTC 时区的时间。原始平台 token、微信 `session_key`、AppSecret 和数据库连接串不得进入业务表。

## 匹配接入数据扩展（Proposed）

以下结构属于 [ADR-0005](../decisions/ADR-0005-matching-api-data-contract.md) 提案。用户已授权实现首批匹配输入，因此表中标为“已实现”的结构已存在于当前任务分支；这不等同于 ADR Accepted 或已合入 `main`。其余结构仍禁止按既成事实描述。

### 结构化匹配输入

| 结构 | Proposed 字段/变化 | 关键约束与兼容策略 |
| --- | --- | --- |
| `match_preferences`（已实现） | `user_id`, `version`, `updated_at` | 一个用户一份匹配偏好；独立乐观锁，避免旧 profile PUT 清空新字段 |
| `project_role_skills`（已实现） | 增加 `required BOOLEAN NOT NULL DEFAULT FALSE` | 历史记录全部为 `false`；同岗位至少保留一个技能；required 必须属于岗位 skills |
| `match_preference_directions`（已实现） | `user_id`, `direction_code`, `position` | FK 到 match preferences；`(user_id, position)` 主键；用户/方向组合唯一；不从简介推断 |
| `match_preference_availability_slots`（已实现） | `user_id`, `position`, `timezone`, `weekday`, `start_minute`, `end_minute` | `(user_id, position)` 主键；`weekday 1..7`，`0 <= start < end <= 1440`；应用层拒绝时间段重叠；P0 仅 `Asia/Shanghai`；每周小时仍保留在 profile |
| `project_roles`（已实现） | 增加 `collaboration_role` | 枚举 `LEADER/MEMBER/FLEXIBLE`；历史迁移为 `MEMBER` |
| `project_role_availability_slots`（已实现） | `role_id`, `position`, `timezone`, `weekday`, `start_minute`, `end_minute` | `(role_id, position)` 主键；空集合表示无硬时间段；非空时用于重叠过滤和时间因素 |
| `project_collaboration_scenarios`（已实现） | `project_id`, `scenario_code`, `position` | `(project_id, position)` 主键；项目/场景组合唯一；应与 profile collaboration scenarios 使用同一受控词表 |
| `experiences` | `id`, `user_id`, `type`, `title`, `direction_code`, `description`, `verification_status`, `visibility`, `started_at`, `ended_at` | 自述与认证分开；AI 不可写 `VERIFIED`；仅公开记录参与他人匹配 |
| `experience_skills` | `experience_id`, `skill_name`, `position` | 使用同一版本化技能词表；不从自由文本自动补标签 |
| `project_members`（已实现） | `id`, `project_id`, `user_id`, `role_id`, `status`, `joined_at` | `(project_id, user_id)` 唯一；`(project_id, role_id)` 复合 FK 保证岗位属于项目；P0 仅 `ACTIVE`；容量计算只统计有效成员 |
| `blocks`（已实现） | `blocker_id`, `blocked_id`, `created_at` | 组合主键唯一，两个用户 FK，数据库禁止自己拉黑；业务双向查询但不暴露方向或原因 |

方向、技能和经历的标准词表版本必须随匹配快照记录。学校层级、性别、微信身份、联系方式、私信和举报数据不进入这些结构化输入。

### 推荐请求与候选快照

| 表 | Proposed 关键字段 | 约束 |
| --- | --- | --- |
| `recommendation_requests`（任务分支已实现） | `id`, `viewer_user_id`, `context`, `expires_at`, `created_at` | ID 使用高熵 opaque 随机值；请求绑定 viewer 和上下文，并带 TTL |
| `recommendation_candidates`（任务分支已实现） | `id`, `request_id`, `rank`, `target_type`, `target_id` | `(request_id, rank)` 和 `(request_id, target_type, target_id)` 唯一；只保存候选索引，不保存敏感原始特征 |
| `recommendation_impressions`（任务分支已实现） | `id`, `request_id`, `viewer_user_id`, `target_type`, `target_id`, `position`, `client_occurred_at`, `received_at` | `(request_id, viewer_user_id, target_type, target_id)` 唯一；candidate 必须属于 request；不同 position 的重复提交冲突 |

`factors_json` 是不可变快照，不作为用户资料或当前匹配真值；其 schema 由 `feature_schema_version` 校验。客户端 cursor 不单独成为业务真值，可使用服务端签名的 opaque token 绑定 request、viewer 和下一 rank。

### 索引、生命周期与安全

- `match_preference_directions(direction_code, user_id)` 支持用户方向候选生成；
- `project_role_skills(skill_name, required, role_id)` 支持岗位技能候选生成；
- `project_members(role_id, status)` 支持容量检查；
- `project_members(user_id, status)` 支持成员授权和后续“我的项目”查询；
- `blocks(blocker_id, blocked_id)` 主唯一索引外，评估反向 `(blocked_id, blocker_id)` 查询；
- `recommendation_requests(viewer_user_id, created_at)` 和 `expires_at` 支持历史查询与 TTL 清理；
- `recommendation_candidates(request_id, rank)` 支持稳定分页；
- `recommendation_impressions(viewer_user_id, received_at)` 支持合规反馈窗口。

读取候选快照不能替代实时授权。返回页面和登记曝光前必须重新检查账号、公开状态、项目/岗位状态、成员容量和双向拉黑。过期请求、候选和曝光的保留周期属于隐私/模型数据政策，当前保持 `TBD`，禁止无期限保留。

## 1. 设计原则

- 核心关系使用数据库约束保证，不只依赖应用代码；
- 个人信息最少收集，公开字段和私有字段明确分离；
- 状态使用受控枚举，不能用任意文本驱动业务；
- 审计字段统一，所有时间使用 UTC；
- AI 生成草稿与用户确认内容分开记录来源；
- 表名、字段名和具体类型在后端框架确定后由迁移文件最终确认。

## 2. 核心实体

| 实体 | 关键字段 | 关键约束 |
| --- | --- | --- |
| User | id, wechat_subject, status, consent_version, created_at | `wechat_subject` 唯一且不可公开 |
| AccountDeletionRequest（任务分支已实现） | id, user_id, status, pending_user_id, requested_at, resolved_at | `pending_user_id` 保证每个用户最多一条 `PENDING` 申请；申请时账号原子进入 `DELETION_PENDING` 并撤销会话 |
| Profile | user_id, nickname, school, major, grade, bio, visibility, version | 一个用户一个当前名片 |
| Skill | id, normalized_name, category, status | 规范名唯一，自定义标签需治理 |
| ProfileSkill | profile_id, skill_id, level, source | 组合唯一 |
| Experience | id, user_id, type, title, description, verification_status | AI 不得把状态改为 verified |
| Availability | user_id, time_slots, hours_per_week | 结构需支持可比较与版本升级 |
| Project | id, owner_id, title, description, direction, stage, status, version | 只有 owner 可管理 |
| ProjectRole | id, project_id, name, headcount, status, availability_requirement | `headcount > 0` |
| ProjectRoleSkill | role_id, skill_id, importance, required | 组合唯一 |
| ProjectMember | project_id, user_id, role_id, status, joined_at | 活跃成员组合唯一 |
| MatchSnapshot | id, subject_id, target_id, direction, score, confidence, engine_type, engine_version, model_version | 仅作解释/分析，不替代成员关系 |
| RecommendationImpression | id, request_id, subject_id, target_id, position, engine_version, occurred_at | 记录实际曝光并去重，训练数据的分母 |
| RecommendationOutcome | id, impression_id, event_type, weight_version, occurred_at | 详情、沟通、邀请、接受和组队等结果，不存消息正文 |
| ModelVersion | id, name, training_run, feature_schema_version, metrics, status, created_at | 登记模型、评估和可回滚状态 |
| Conversation | id, project_id, created_at | 参与关系单独保存 |
| ConversationParticipant | conversation_id, user_id, status | 组合唯一 |
| Message | id, conversation_id, sender_id, type, content, status, created_at | 发送者必须是会话参与者 |
| Invitation | id, project_id, role_id, inviter_id, invitee_id, status, expires_at | 接受操作幂等 |
| Block | blocker_id, blocked_id, created_at | 组合唯一，不允许自己拉黑自己 |
| Report（任务分支已实现提交记录） | id, reporter_id, target_type, target_id, reason, description, status, pending_key, created_at | 目标类型/原因/状态受约束；`pending_key` 保证同一 reporter、目标、原因最多一条 `PENDING`；正文仅供治理，不进入推荐或日志 |
| AuditEvent（任务分支已实现最小写入） | id, actor_user_id, action, resource_type, resource_id, request_id, outcome, created_at | 举报首次提交和注销首次申请同事务写入；不存密钥、举报说明和完整敏感正文 |

## 3. 关系概览

```text
User 1--1 Profile
User 1--N Experience
Profile N--N Skill
User 1--N Project (owner)
Project 1--N ProjectRole
ProjectRole N--N Skill
Project N--N User (through ProjectMember)
User N--N Conversation
Conversation 1--N Message
ProjectRole 1--N Invitation
User N--N User (through Block)
User 1--N Report
MatchSnapshot 1--N RecommendationImpression
RecommendationImpression 1--N RecommendationOutcome
```

## 4. 状态机

### Project

`DRAFT -> PUBLISHED -> CLOSED`

- `DRAFT` 不出现在大厅和匹配中；
- `PUBLISHED` 必须有至少一个开放岗位；
- `CLOSED` 不接受新邀请；重新开放是否允许需在实现前确认。

### Invitation

`PENDING -> ACCEPTED | REJECTED | EXPIRED | CANCELLED`

只有 `PENDING` 可首次接受或拒绝；重复接受 `ACCEPTED` 和重复拒绝 `REJECTED` 返回原确定结果。接受时必须原子创建成员关系并更新邀请状态，成员容量由有效成员计数导出。

第五版实现使用 `pending_key = project_id:role_id:invitee_id` 保证同一组合最多一条 `PENDING` 邀请；进入终态时清空该键，允许后续重新邀请。`expires_at`、`created_at` 和 `responded_at` 使用 UTC；首版有效期为 7 天，该时长仍需角色 A 评审。过期邀请在读取/处理时判定，当前不依赖定时任务。

### Conversation / Message

- 第六版 `conversation_key = project_id:sorted_user_a:sorted_user_b`，保证同一项目与同一对用户只有一个会话；
- 每个首版会话恰有两个 `ACTIVE` 参与者；数据库通过 `(conversation_id, sender_id)` 复合外键保证消息发送者属于该会话；
- `(sender_id, client_message_id)` 唯一，发送操作在会话行锁内处理同 key 重试和正文冲突；
- `messages(conversation_id, created_at, id)` 支持稳定正序分页，`conversation_participants(user_id, status, conversation_id)` 支持私有会话列表；
- 消息正文属于 Sensitive，不进入日志、推荐特征或训练事件；长度与纯文本校验由服务/API 层执行，数据库保留类型、状态、参与关系和唯一性约束。

### User

`ACTIVE -> SUSPENDED | DELETION_PENDING -> DELETED/ANONYMIZED`

具体注销等待期与保留范围由隐私政策和适用要求确认。

## 5. 隐私分类

| 分类 | 示例 | 处理要求 |
| --- | --- | --- |
| Public | 用户主动公开的昵称、技能、项目摘要 | 仍需可撤回公开，禁止无限复制 |
| Internal | 用户 ID、匹配分项、举报状态 | 仅业务所需角色和服务访问 |
| Sensitive | 微信身份标识、联系方式、私信正文、未公开经历 | 加密传输、严格授权、最小日志 |
| Secret | 会话签名密钥、微信密钥、数据库凭证、AI API Key | 仅密钥管理/运行环境，永不进入业务表和仓库 |

## 6. 索引与查询

具体索引由真实查询计划决定，首版至少评估：

- 用户微信身份唯一索引；
- 项目状态、发布时间和方向组合查询；
- 岗位状态与项目外键；
- 技能关联的双向索引；
- 会话参与者和消息时间分页；
- 邀请的被邀请者、状态和过期时间；
- 拉黑双向查询；
- 举报状态和创建时间。

不要在没有 `EXPLAIN` 或负载证据时盲目增加大量索引。

## 7. 迁移规则

- 每次 schema 变化必须有向前迁移、兼容性说明和回滚/修复策略；
- 迁移先在测试和 staging 数据副本验证；
- 破坏性字段变更采用“新增 -> 双写/回填 -> 切读 -> 删除”的分阶段方式；
- 不允许在生产手工执行未进入版本控制的 DDL；
- 测试必须覆盖唯一约束、外键、状态转换和重复请求。
