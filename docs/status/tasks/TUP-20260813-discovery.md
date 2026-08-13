# TUP-20260813-discovery：发现与检索

> Status: Ready for Review<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `43dc95e`<br>
> Branch: `role-b/feature/TUP-20260813-discovery`<br>
> Last Updated: 2026-08-13

## 1. 目标

实现后端 MVP 的发现与检索切片：项目大厅、人才大厅、公开名片详情和当前用户项目列表，补齐 `API-DISC-01`、`API-DISC-02`、`API-PROF-03` 及 `GAP-PROJ-03` 的可运行接口。

## 2. 范围

- memory/SQL 两种存储适配器的发现查询；
- 项目按方向、赛事、技能、阶段、状态筛选，按最新发布时间稳定游标分页；
- 人才按公开状态、技能、方向、合作偏好和投入时间筛选，双向拉黑过滤；
- 公开名片详情只返回公开字段，并对未公开/不可见资源统一返回不可见；
- 当前用户的项目列表按状态筛选并稳定分页；
- API、测试和本任务记录同步。

## 3. 非目标

- 不开放 Guest 匿名浏览；`IA-GAP-01` 尚未由角色 A 确认，本任务采用“先要求登录”的可逆假设；
- 不实现推荐匹配 API、推荐快照/曝光事件或模型重排；
- 不引入搜索引擎、向量数据库、缓存或新的生产依赖；
- 不实现管理员下架、举报治理和注销流程。

## 4. 负责人、评审方与影响

- 修改方：角色 B；
- 评审方：角色 A，重点确认 Guest 访问策略、公开名片字段和筛选参数；
- 接口影响：新增 `GET /api/v1/profiles/{profileId}`、`GET /api/v1/profiles`、`GET /api/v1/me/projects`，扩展 `GET /api/v1/projects` 查询参数；
- 数据影响：仅增加查询，不新增表或迁移；
- 安全影响：服务端执行公开状态、账号状态和双向拉黑过滤，避免 IDOR 与隐私泄漏。

## 5. 基线与同步

- 基线提交：`43dc95e`；
- `git fetch --prune origin` 于本轮早期执行成功，当时远端未存在同名分支；最终提交前直连和 `127.0.0.1:7897` 代理重试均在 60 秒超时，因此不能把最终同步记为成功。

## 6. 验收标准

- 未认证请求不能访问本切片的受保护发现接口；
- 项目列表只返回 `PUBLISHED`/显式筛选状态允许的项目，并正确执行全部筛选条件和稳定分页；
- 人才列表和详情只返回主动公开且账号正常的名片，双方任一方向拉黑后不可见；
- 当前用户项目列表只返回自己的项目，不泄露他人草稿；
- memory 与 MySQL 查询行为、错误码和分页语义一致；
- `python -m pytest -ra`、编译检查和变更 Markdown 链接检查结果写入本文件。

## 7. 进展

- [x] 创建独立分支和任务文件；
- [x] 实现 DTO、memory/SQL 查询和路由；
- [x] 增加筛选、权限、拉黑和分页测试；
- [x] 同步 API 契约和评审入口；
- [x] 完成验证并记录剩余风险。

## 8. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `git fetch --prune origin` | Partial | 本轮早期成功；最终提交前直连和 7897 代理重试均超时，需网络恢复后再次同步 |
| `python -m pytest -ra`（MySQL 8.4.11） | Passed | 80 passed；包含 discovery、项目详情可见性和非活跃账号过滤的真实 MySQL 验证 |
| `python -m alembic upgrade head / downgrade base / upgrade head` | Passed | 一次性 MySQL 8.4.11 测试库完成迁移往返，最终位于 `20260813_0010 (head)` |
| `python -m compileall -q app tests migrations` | Passed | 应用、测试与迁移模块编译通过 |
| `git diff --check` | Passed | 无空白错误 |
| changed Markdown relative-link check | Passed | 本轮 PowerShell 相对链接检查无缺失目标 |

## 9. 当前状态与剩余风险

- 发现接口已在 memory/SQL 两种适配器实现，等待角色 A 评审；
- Guest 匿名浏览仍由 `IA-GAP-01` 阻塞，本任务采用先认证的可逆假设；
- 项目和人才筛选当前为精确匹配，复杂全文搜索、排序白名单扩展和搜索基础设施不在范围；
- 发现查询、已知 ID 详情访问、双向拉黑和账号待注销过滤已在一次性 MySQL 8.4.11 测试库验证；该测试库不代表 staging 环境；
- Guest 匿名策略、复杂搜索和 staging 性能基线仍待后续评审。
