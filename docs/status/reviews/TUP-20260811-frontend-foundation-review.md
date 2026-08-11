# TUP-20260811：微信小程序前端基础评审

> Status: Proposed<br>
> Owner: 角色 B<br>
> Requested By: 角色 A<br>
> Review Target: `role-a/feature/TUP-20260811-frontend-foundation`<br>
> Review State: Pending<br>
> Target Commit: 以远程评审分支 HEAD 为准；评审人必须填写实际 `Reviewed Commit`<br>
> Last Updated: 2026-08-11

## 1. 目标

核对角色 A 的 UniApp 微信小程序基础工程是否遵守现有产品流程、合约缺口与安全边界，并确认可以在 OpenAPI/DTO 完成后接入真实后端。本评审不确认新的公共 API 或数据字段，也不要求创建 PR。

## 2. 评审范围

- 任务：`TUP-20260811-frontend-foundation`
- 需求：`AUTH-001`、`PROF-001/002`、`PROJ-001`
- 代码：`apps/miniapp/`
- 文档：`docs/development/DEVELOPMENT.md`、任务文件和本评审文件
- 非范围：真实微信登录、token、后端实现、数据库、匹配算法、消息和部署

## 3. 必查项

1. `src/services/runtime.ts`、`repository.ts` 与 `storage.ts` 是否确保 API 模式不会模拟登录、保存或发布成功，fixture 是否始终带 `PROPOSED_GAP` 和 `GAP-*` 来源。
2. 客户端是否未存储微信 code、token、密钥、他人非公开资料或生产数据；本地恢复草稿是否只包含当前用户输入。
3. 页面是否只通过 `src/services/` 访问数据，且未把 owner、401/403、409、发布幂等或权限判断错误地当成客户端安全保证。
4. 登录 -> 名片 -> 我的 -> 项目/岗位 -> 预览 -> 发布结果是否与 `USER_FLOWS.md`、`SCREEN_SPEC.md` 一致；校验失败和未保存退出是否保留输入。
5. `GAP-AUTH-01/02`、`GAP-PROF-01/02`、`GAP-PROJ-01..04` 是否仍被清楚标记为待定，手写 fixture 是否没有冻结成真实 DTO。
6. 微信小程序构建、触控尺寸、安全区、底部导航和表单控件是否可在微信开发者工具中正常运行。

## 4. 建议验证命令

在干净工作区检出目标提交后执行：

```bash
cd apps/miniapp
npm ci
npm run type-check
npm test
npm run build:demo:mp-weixin
npm run build:mp-weixin
```

可选：运行 `npm run dev:mp-weixin`，在微信开发者工具导入 `apps/miniapp/dist/dev/mp-weixin`，手动检查登录、输入、picker、switch、返回确认和发布流程。

## 5. 可直接交给角色 B Codex 的提示词

```text
按 TeamUp 根 AGENTS.md 审查 role-a/feature/TUP-20260811-frontend-foundation。
只做代码与契约使用评审，不修改角色 A 的任务文件、产品规范、API、数据模型或安全规范，不创建 PR，不 merge main。
逐项核对 docs/status/reviews/TUP-20260811-frontend-foundation-review.md 第 3 节，并实际运行第 4 节命令。
优先报告 fixture 泄漏到生产、认证/权限伪成功、敏感数据存储、契约漂移、未保存数据丢失、重复发布、微信端构建或交互问题。
每个问题给文件/行号、触发条件、影响和可执行修复方向；只填写本文件第 6 节，或通过 QQ 返回可原样落盘的完整第 6 节 Markdown。
```

## 6. 角色 B 评审结论（待填写）

> Reviewer: 角色 B<br>
> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

### 6.1 问题

| ID | Severity | File / Line | Trigger / Impact | Required Fix |
| --- | --- | --- | --- | --- |
| FE-REV-001 | TBD | TBD | TBD | TBD |

没有问题时将占位行替换为“无”，并说明微信开发者工具、真实 API 和真机尚未覆盖的剩余风险。

### 6.2 契约与安全结论

| Area | Decision | Reason / Required Action |
| --- | --- | --- |
| Fixture / API 模式隔离 | `Accept / Change` | TBD |
| 登录与本地存储边界 | `Accept / Change` | TBD |
| Profile `GAP-*` 使用 | `Accept / Change` | TBD |
| Project `GAP-*` 使用 | `Accept / Change` | TBD |
| 401/403/409 与重复提交 | `Accept / Change` | TBD |
| 微信端构建与交互 | `Accept / Change` | TBD |

### 6.3 验证与批准

- 实际执行的检查：TBD
- 未执行检查：TBD
- 剩余风险：TBD
- 允许集成到 `main`：`Yes / No`
- 允许进入真实 OpenAPI 适配任务：`Yes / No`

## 7. 返回方式

角色 A 提交并推送任务分支后，通过 QQ 发送分支名、目标 commit 和本文件路径。角色 B 可在自己的评审分支中只填写第 6 节，或通过 QQ 返回可原样落盘的完整第 6 节；需要变更公共契约时另建唯一负责人任务。
