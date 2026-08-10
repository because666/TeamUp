# TUP-20260810：前后端对接指南角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-a/docs/TUP-20260810-role-a-product-backend`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-10

## 1. 评审目标

核对 [前后端对接与联调指南](../../development/FRONTEND_BACKEND_INTEGRATION.md) 是否能支持前端并行实现和 P0 首条纵向切片，重点检查页面状态、mock 约束、错误映射、接口映射、Fork/Git 交付和 staging 验收要求。

## 2. 评审步骤

```bash
git status --short --branch
git fetch --prune <共享仓库远程名>
git switch --detach <评审远程>/role-a/docs/TUP-20260810-role-a-product-backend
git diff --stat <基线提交>...HEAD
```

阅读：

- `docs/development/FRONTEND_BACKEND_INTEGRATION.md`
- `docs/architecture/API_CONTRACT.md`
- `docs/product/PRD.md`
- `docs/product/SCREEN_SPEC.md`（存在后）
- `docs/development/GIT_WORKFLOW.md`

## 3. 必查问题

- P0 登录 -> 名片 -> 项目发布是否覆盖正常、loading、空、错误、401、403、409 和重复提交状态；
- API ID、字段命名和错误码是否足以让前端使用 mock 并切换真实后端；
- mock 是否明确不是第二份契约，且没有把服务端权限逻辑移到前端；
- 真实微信登录、local/test 替代方案和生产配置边界是否清楚；
- 分支、任务、评审、契约 SHA 和交付证据是否能被另一位开发者恢复；
- 是否存在会阻塞前端初始化的未决工具链、OpenAPI 或 staging 信息。

## 4. 评审结论（待填写）

> Reviewer: 角色 A<br>
> Reviewed Commit: `TBD`<br>
> Reviewed At: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

### 4.1 阻塞问题

| ID | File / Section | Trigger | Impact | Required Fix |
| --- | --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD | TBD |

没有阻塞问题时，将占位行替换为“无”，并说明测试缺口或剩余风险。

### 4.2 非阻塞问题

| ID | File / Section | Observation | Suggested Follow-up |
| --- | --- | --- | --- |
| NB-001 | TBD | TBD | TBD |

### 4.3 验证与下一步

- 实际执行的检查：`TBD`
- 未执行的检查及原因：`TBD`
- 允许角色 B 继续后端工程初始化：`Yes / No`
- 下一步负责人和任务：`TBD`

评审完成后，角色 A 只需修改本文件第 4 节，或把完整 Markdown 原样交给角色 B 落盘。QQ 仅用于通知文件位置。
