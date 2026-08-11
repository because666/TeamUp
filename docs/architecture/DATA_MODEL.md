# TeamUp 核心数据模型

> Status: Proposed<br>
> Owner: 角色 B<br>
> Reviewers: 角色 A<br>
> Last Updated: 2026-08-10

## 基础实现状态

首个 FastAPI 切片在 local/test 内存适配器中映射了 `User`、`Profile`、`Project` 和 `ProjectRole`。该适配器不构成生产持久化决策；进入 staging 或 production 前仍需完成 MySQL 表、约束、迁移和回滚验证。

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
| Report | id, reporter_id, target_type, target_id, reason, status | 处理动作需审计 |
| AuditEvent | id, actor_id, action, resource_type, resource_id, request_id, created_at | 不存密钥和完整敏感正文 |

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

只有 `PENDING` 可接受或拒绝。接受时必须原子创建成员关系并更新岗位容量。

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
