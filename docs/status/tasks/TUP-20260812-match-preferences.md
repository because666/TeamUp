# TUP-20260812-match-preferences: 匹配偏好与岗位匹配字段

> Status: Ready for Review<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `1c31456`<br>
> Branch: `role-b/feature/TUP-20260812-match-preferences`<br>
> Last Updated: 2026-08-12

## 1. 实施授权

用户于 2026-08-12 明确要求按 ADR-0005 推荐方案继续。该明确批准满足仓库对公共 API/数据变更的实施授权要求；ADR-0005 仍保持 Proposed，角色 A 必须在合入 `main` 前评审前端字段、兼容行为和交互。

## 2. 目标

实现 `match-v0.1` 首批结构化输入：用户方向/时间偏好、岗位 required skill、岗位时间要求、岗位协作身份和项目协作场景，并保持现有客户端字段兼容。

## 3. 范围

- `GET/PUT /api/v1/me/match-preferences`；
- `MatchPreferences`、方向和可用时间段 MySQL 表及内存适配；
- 岗位技能 `required` 标记、岗位时间段和 `collaborationRole`；
- 项目 `collaborationScenarios`；
- 现有项目创建/更新/读取 DTO 的兼容处理；
- Alembic 向前/向后迁移；
- DTO、API、repository、SQLite 和真实 MySQL 测试；
- API、数据、迁移和任务文档同步。

## 4. 非目标

- 不实现经历和专业分类；
- 不实现成员容量、拉黑、推荐请求快照或曝光；
- 不发布 `API-MATCH-01/02/03`；
- 不改变 `match-v0.1` 权重；
- 不合入 `main`，直到角色 A 评审。

## 5. 接口与兼容边界

- 新接口：`API-MATCH-PREF-01/02`；
- 现有岗位 `skills` 保持全部目标技能；`requiredSkills` 必须是其子集；
- 历史技能迁移为 `required=false`；
- 创建时省略新岗位字段使用安全默认值；更新时省略表示保留现值；
- 时间段 P0 仅接受 `Asia/Shanghai`；
- 所有写操作服务端鉴权、校验和乐观锁。

## 6. 计划

- [x] 创建独立任务并记录用户实施授权；
- [x] 扩展 API DTO 和统一校验；
- [x] 实现 memory/MySQL repository；
- [x] 创建第二版 Alembic 迁移；
- [x] 接入 FastAPI 路由和 OpenAPI；
- [x] 增加兼容、权限、版本和真实 MySQL 测试；
- [x] 同步文档并建立角色 A 评审入口。

## 7. 验收标准

- [x] 偏好创建、读取、更新和版本冲突正确；
- [x] 非法/重叠时间段、重复方向和 required 非子集被拒绝；
- [x] 旧项目 payload 仍可创建和更新，不清空既有新字段；
- [x] 历史技能在迁移后全部为 bonus；
- [x] migration upgrade/downgrade 和 ORM schema 一致；
- [x] 现有 API 和匹配规则测试不回归。

## 8. 计划修改文件

- `services/api/app/schemas.py`、`store.py`、`db_models.py`、`sql_store.py`、`main.py`；
- `services/api/migrations/versions/*`、相关测试；
- `docs/architecture/API_CONTRACT.md`、`DATA_MODEL.md`、迁移和状态文档。

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git fetch --prune origin` via `127.0.0.1:7897` | Passed | 基线 `1c31456` 已推送 |
| `python -m pytest -ra` with disposable MySQL 8.4 | Passed | 47 tests；包含真实 MySQL repository/API、内存 API、SQLite repository 和迁移回归 |
| `python -m alembic check` against MySQL 8.4 | Passed | ORM 与 `20260812_0002` 无 schema 漂移 |
| `upgrade head -> downgrade base -> upgrade head` against MySQL 8.4 | Passed | 第二版迁移前进、回滚和重建均通过；一次性测试容器已删除 |
| 历史 `20260811_0001` 数据升级 | Passed | 历史技能 `required=false`，历史岗位 `collaboration_role=MEMBER` |
| `python -m compileall -q app tests` | Passed | 应用与测试模块编译通过 |
| changed Markdown relative-link check | Passed | 8 个变更 Markdown 文件的相对链接有效 |
| `git diff --check` | Passed | 无空白错误 |

## 10. 当前状态与下一步

- 当前：实现、迁移、文档和验证已完成，进入角色 A 评审。
- 下一步：角色 A 在 `docs/status/reviews/TUP-20260812-match-preferences-review.md` 评审；通过前不合入 `main`。
- 剩余风险：方向、技能别名和协作场景受控词表仍待角色 A 提供；当前只做长度、去重、子集和时间范围等结构校验。
- 非本任务能力：经历、成员容量、拉黑、推荐快照、匹配列表和曝光仍未实现。
- 最后相关提交：`feat(matching): add preferences and role constraints`
