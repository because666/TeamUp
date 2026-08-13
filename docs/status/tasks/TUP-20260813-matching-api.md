# TUP-20260813-matching-api：规则匹配 API

> Status: Ready for Review<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `e56a8f7`<br>
> Branch: `role-b/feature/TUP-20260813-matching-api`<br>
> Last Updated: 2026-08-13

## 1. 目标

把已验证的 `match-v0.1` 规则引擎接成岗位粒度匹配接口，补齐 `API-MATCH-01` 和 `API-MATCH-02` 的认证、资源授权、硬约束、解释因素和稳定分页。

## 2. 范围

- `GET /api/v1/projects/{projectId}/matches?roleId=...` 项目岗位候选成员；
- `GET /api/v1/me/project-matches` 当前用户候选项目岗位；
- memory/SQL 两种存储适配器的规则匹配查询；
- 公开状态、账号状态、项目/岗位状态、容量、成员关系和双向拉黑过滤；
- `requiredSkills` 与必需时间段硬约束；
- `MatchResult` 解释 DTO、规则版本、缺失信息和不透明分页游标；
- 进程内短期候选快照，仅用于本任务稳定翻页验证。

## 3. 非目标

- 不新增 `recommendation_requests`、`recommendation_candidates` 或曝光表；
- 不实现 `API-MATCH-03` 推荐曝光、结果事件、训练数据和模型重排；
- 不从专业、简介、学校或经历自由文本推断匹配分数；
- 不改动已确认的匹配权重和规则 golden tests。

## 4. 负责人、评审方与影响

- 修改方：角色 B；
- 评审方：角色 A，重点确认岗位粒度、候选摘要、硬约束和低置信结果展示；
- 接口影响：新增 `API-MATCH-01`、`API-MATCH-02`；
- 数据影响：本轮无迁移；快照仅进程内保存，重启后 cursor 失效；
- 安全影响：服务端执行 owner、公开、账号状态、容量、成员和双向拉黑检查，不返回治理原因或非公开资料。

## 5. 基线与同步

- 当前工作区包含 discovery 任务未提交改动，未做 reset/覆盖；
- `git fetch --prune origin` 于本轮早期执行成功；最终提交前直连和 `127.0.0.1:7897` 代理重试均在 60 秒超时，提交前仍需恢复网络后复查。

## 6. 验收标准

- `API-MATCH-01` 仅项目 owner 可调用，项目/岗位无效状态、满员、非 owner 和越权访问有稳定错误码；
- `API-MATCH-02` 仅使用当前用户完整名片，未完成名片返回 `MATCH_PROFILE_INCOMPLETE`；
- 两个方向均过滤草稿、关闭、隐藏、非活跃、成员、容量和双向拉黑目标；
- required skill/时间段不满足的候选不出现在结果中；
- 返回 score、confidence、informationSufficient、engineVersion、factors 和 missingInformation，不返回 rankingScore；
- 首次响应签发 opaque recommendationRequestId，后续 cursor 绑定请求者和上下文，非法/过期 cursor 显式失败；
- memory 与 SQL 行为一致，API 和存储测试通过。

## 7. 进展

- [x] 创建任务记录并确认 ADR-0005 Proposed 边界；
- [x] 实现匹配 DTO、规则适配和候选快照；
- [x] 实现 memory/SQL 查询与 API 路由；
- [x] 增加权限、硬约束、拉黑、分页和持久化测试；
- [x] 同步契约与角色 A 评审入口；
- [x] 完成验证并记录剩余风险。

## 8. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `python -m pytest -ra`（MySQL 8.4.11） | Passed | 80 passed；包含匹配请求、候选快照、曝光和非活跃账号过滤的真实 MySQL 验证 |
| `python -m alembic upgrade head / downgrade base / upgrade head` | Passed | MySQL 8.4.11 迁移往返通过 |
| `python -m compileall -q app tests migrations` | Passed | 应用、测试与迁移模块编译通过 |
| `git diff --check` | Passed | 无空白错误 |
| changed Markdown relative-link check | Passed | 本轮 PowerShell 相对链接检查无缺失目标 |

## 9. 当前状态与剩余风险

- `API-MATCH-01/02` 已在 memory/SQL 两种适配器实现，等待角色 A 评审；
- `recommendationRequestId`/cursor 是进程内短期快照，重启失效，不能替代 ADR-0005 的持久化推荐快照；
- `API-MATCH-03` 曝光、推荐结果事件、模型重排和训练数据尚未实现；
- 真实 MySQL 匹配、候选快照和曝光链路已验证，并修复父请求与候选的外键插入顺序；
- 专业、经历和更丰富时间段语义保持缺失或 Proposed，未从自由文本推断。
