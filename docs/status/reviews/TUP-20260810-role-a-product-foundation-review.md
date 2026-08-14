# TUP-20260810：角色 A 产品基础技术评审

> Status: Proposed<br>
> Owner: 角色 B<br>
> Requested By: 角色 A<br>
> Review Target: `role-a/docs/TUP-20260810-role-a-product-foundation`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-10

## 1. 目标

核对角色 A 定义的登录 -> 名片 -> 项目发布流程是否能在现有 API、数据和安全边界内实现，并对 `GAP-*` 给出技术结论。本评审不要求创建 PR，不授权角色 B 的 AI 直接改产品或公共契约。

## 2. 获取评审版本

工作区必须干净；存在未提交改动时停止切换并先处理自己的工作。

```bash
git fetch --prune origin
git switch --detach origin/role-a/docs/TUP-20260810-role-a-product-foundation
git status --short --branch
git log -1 --oneline
git diff --stat origin/role-a/docs/TUP-20260810-docs-baseline...HEAD
```

不要发起 GitHub OAuth/device 授权，不需要创建 PR，不要 merge `main`。

## 3. 必读与必查

阅读：

- `docs/product/USER_FLOWS.md`
- `docs/product/INFORMATION_ARCHITECTURE.md`
- `docs/product/SCREEN_SPEC.md`
- `docs/architecture/API_CONTRACT.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/security/SECURITY_AND_PRIVACY.md`

必须核对：

1. `GAP-AUTH-01/02`：同意版本、会话返回和名片完成状态能否安全实现；拒绝同意是否保持 Guest。
2. `GAP-PROF-01/02`：无名片语义、版本冲突、合作场景和角色偏好的字段/公开范围是否完整。
3. `GAP-PROJ-01..04`：项目与岗位写入、我的项目列表、发布前置、owner/公开 DTO 边界是否可实现。
4. `401/403/409`、资源所有权、重复发布、状态恢复和本地草稿处理是否存在越权或数据覆盖风险。
5. 页面是否把 Proposed `GAP-*` 误写成已确认接口；是否遗漏会阻塞首条切片的 API、数据、安全或隐私问题。

## 4. 可直接交给角色 B Codex 的提示词

```text
按 TeamUp 根 AGENTS.md 审查 role-a/docs/TUP-20260810-role-a-product-foundation。
只做技术评审，不修改产品文档、API、数据模型或安全规范，不创建 PR，不 merge main。
逐项核对 docs/status/reviews/TUP-20260810-role-a-product-foundation-review.md 第 3 节。
优先报告接口不可实现、字段缺失、资源越权、隐私泄漏、状态/幂等/并发和契约漂移风险。
每个问题给文件/行号、触发条件、影响和修复方向；逐个给 8 个 GAP 的 Accept / Change / Split 结论。
只填写本评审文件第 5 节，或把第 5 节完整 Markdown 通过 QQ 原样返回角色 A。不能只回复“没问题”。
```

## 5. 角色 B 评审结论（待填写）

> Reviewer: 角色 B<br>
> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

### 5.1 问题

| ID | Severity | File / Line | Trigger / Impact | Required Fix |
| --- | --- | --- | --- | --- |
| PF-REV-001 | TBD | TBD | TBD | TBD |

没有问题时将占位行替换为“无”，并说明测试缺口和剩余风险。

### 5.2 GAP 结论

| Gap | Decision | Reason / Contract Action |
| --- | --- | --- |
| `GAP-AUTH-01` | `Accept / Change / Split` | TBD |
| `GAP-AUTH-02` | `Accept / Change / Split` | TBD |
| `GAP-PROF-01` | `Accept / Change / Split` | TBD |
| `GAP-PROF-02` | `Accept / Change / Split` | TBD |
| `GAP-PROJ-01` | `Accept / Change / Split` | TBD |
| `GAP-PROJ-02` | `Accept / Change / Split` | TBD |
| `GAP-PROJ-03` | `Accept / Change / Split` | TBD |
| `GAP-PROJ-04` | `Accept / Change / Split` | TBD |

### 5.3 验证与批准

- 实际执行的检查：TBD
- 未执行检查：TBD
- 剩余风险：TBD
- 允许角色 A 依据本文进入前端原型：`Yes / No`
- 允许相应契约任务开始：`Yes / No`

## 6. 返回方式

角色 A 通过 QQ 发送分支名和本文件路径。角色 B 可以把第 5 节完整 Markdown 原样发回，或在自己的评审分支中只填写本文件第 5 节并推送。需要修改 API、数据或安全规范时，先在本文件记录结论，再由对应负责人建立独立契约任务。
