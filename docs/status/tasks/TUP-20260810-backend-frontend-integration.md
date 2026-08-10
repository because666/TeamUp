# TUP-20260810-backend-frontend-integration：前后端对接基线

> Status: Proposed<br>
> Owner: 角色 B<br>
> Reviewer: 角色 A<br>
> Base Commit: `167edd5`<br>
> Branch: `role-a/docs/TUP-20260810-role-a-product-backend`<br>
> Last Updated: 2026-08-10

## 1. 目标

建立一份可直接执行的前后端契约、mock、联调、Fork/Git 和交付流程，使角色 A、B 能在工程尚未初始化时先对齐契约，并在初始化后沿同一流程完成首条 P0 纵向切片。

## 2. 依据

- PRD：`AUTH-001`、`PROF-001/002`、`PROJ-001`
- API：`API-AUTH-01`、`API-PROF-01/02`、`API-PROJ-01/02/03/04`
- ADR：ADR-0001、ADR-0003

## 3. 范围

- 新增 `docs/development/FRONTEND_BACKEND_INTEGRATION.md`；
- 定义职责、契约冻结、并行开发、mock、本地/staging 联调和验收矩阵；
- 定义契约缺口、Fork/分支、评审和交付流程；
- 更新文档索引；
- 新增角色 A 的独立评审记录模板；
- 由角色 A 评审产品、页面状态和前端执行可行性。

## 4. 非目标

- 不初始化前端或后端工程；
- 不替代 ADR-0001 选择后端框架；
- 不新增、删除或确认具体 API DTO 和数据库 schema；
- 不虚构安装、启动、测试、部署命令或 staging 地址；
- 不 commit、push、merge 或部署。

## 5. 依赖与假设

- 当前工作基线为 `origin/role-a/docs/TUP-20260810-role-a-product-backend` 的初始提交，文档基线尚未集成到 `main`；
- API 和数据文档仍为 `Proposed`，实现前需要双方逐项确认；
- 当前本地只配置了名为 `origin` 的共享仓库远程，文档不假设双方 fork 的远程名称相同；
- 工程初始化后，双方必须把实际验证的命令回填到开发指南。

## 6. 计划

- [x] 阅读 API、数据、PRD、安全、Git 和 AI 协作文档
- [x] 编写前后端对接与联调指南
- [x] 建立首条 P0 纵向切片和 API 映射
- [x] 增加 mock、错误处理、测试和契约变更规则
- [x] 更新文档索引和任务记录
- [x] 创建角色 A 评审记录模板
- [ ] 角色 A 完成前端/产品可执行性评审

## 7. 验收标准

- [x] 双方职责、权威文件和共享文件唯一编辑者清晰
- [x] 首条联调路径可追溯到 PRD/API ID
- [x] mock 不成为第二份契约，生产禁用要求明确
- [x] 401/403/409、重复提交、版本冲突和隐私测试已列入矩阵
- [x] Fork、分支、评审、集成和交付物规则可执行
- [x] 所有未确定工具、命令和环境保持 `TBD` 或待确认
- [ ] 角色 A 给出 `Approved` 或 `Changes Requested`

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-10 | 创建前后端对接基线 | 支持两人分别开发前后端并减少契约漂移和联调返工 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| 文档相对链接检查 | Passed | PowerShell 相对链接解析，全部目标存在 |
| `git diff --check` | Passed | 无 whitespace error |
| 敏感信息检查 | Passed | 常见 API key、云密钥和私钥模式无命中 |
| 前后端构建/测试 | Not run | 工程尚未初始化，本任务不包含代码 |

## 10. 当前状态与下一步

- 最后完成：对接指南、P0 API 映射、联调矩阵和契约变更流程已建立。
- 当前阻塞：无；实际工程命令依赖前后端初始化，后端初始化依赖 ADR-0001。
- 下一步：执行文档检查后，请角色 A 评审前端流程和页面状态是否可执行。
- 最后相关提交：`uncommitted`
