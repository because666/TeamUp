# TUP-20260810：角色 B 文档与技术基线评审

> Status: Proposed<br>
> Owner: 角色 B<br>
> Requested By: 角色 A<br>
> Review Target: `role-a/docs/TUP-20260810-docs-baseline`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-10

## 1. 目标

角色 B 核对当前文档基线是否足以约束后端、数据、安全和双人 Codex 协作，并给出可落盘、可追溯的批准或修改请求。Pull Request 不是本次评审的前提。

## 2. 获取评审版本

先在角色 B 的 TeamUp 仓库运行 `git status --short --branch`。如果存在未提交改动，停止切换分支并先处理自己的工作；不要 reset、restore 或覆盖。

工作区干净时执行：

```bash
git fetch --prune origin
git switch --detach origin/role-a/docs/TUP-20260810-docs-baseline
git status --short --branch
git log -1 --oneline
git diff --stat origin/main...HEAD
```

评审源应为远程分支 `origin/role-a/docs/TUP-20260810-docs-baseline`。不要发起 GitHub OAuth/device 授权，不需要创建 PR。

## 3. 必读文件与必查问题

### A. AI 与文件协作规则

阅读：

- `AGENTS.md`
- `docs/development/AI_WORKFLOW.md`
- `docs/development/GIT_WORKFLOW.md`
- `docs/decisions/ADR-0003-two-person-ai-workflow.md`

必须确认：一任务一负责人/分支/任务文件是否可执行；QQ 是否明确只用于通知；评审、决定、交接和状态是否都要求写回仓库；PR 可选但跨角色评审不可省略；AI 的 commit、push、merge、部署和危险操作边界是否足够明确。

### B. 后端框架决策

阅读 `docs/decisions/ADR-0001-backend-framework.md`，由角色 B 明确记录：

- 自己对 FastAPI、Spring Boot 的实际熟练度和维护把握；
- 推荐选择、理由，以及是否需要半天纵向 spike；
- MySQL 迁移、OpenAPI、认证授权、事务、测试、容器和腾讯云运维是否存在遗漏；
- ADR-0001 应 `Accepted`，还是保持 `Proposed` 并列出尚缺证据。

不要只用“AI 更适合某语言”作为选择理由。

### C. 推荐与小模型可行性

阅读：

- `docs/decisions/ADR-0002-mvp-ai-scope.md`
- `docs/architecture/MATCHING.md`
- `docs/architecture/ML_RECOMMENDER.md`

必须确认：P0 规则过滤/排序是否能由后端稳定实现；推荐事件和特征 schema 是否可存储、去重、脱敏和删除；P1 逻辑回归基线、时间切分、影子运行、版本登记和规则回退是否可实施；模型是否始终不能绕过权限、拉黑、岗位容量和隐私硬约束。

### D. API、数据、安全与隐私缺口

阅读：

- `docs/architecture/API_CONTRACT.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/security/SECURITY_AND_PRIVACY.md`
- `docs/product/PRD.md`
- `docs/product/MVP_SCOPE.md`

至少检查：微信登录和会话撤销、资源级授权/IDOR、项目与岗位状态、重复请求与幂等、邀请并发、拉黑后的消息和邀请、公开/私有字段、日志脱敏、注销/删除与训练派生数据、举报审计、错误码和分页契约。发现缺口时给出文件、章节或行号、影响和建议修复方向。

## 4. 可直接交给角色 B Codex 的提示词

```text
你是 TeamUp 的角色 B Codex。按仓库根 AGENTS.md 执行一次只读技术评审。

评审源：origin/role-a/docs/TUP-20260810-docs-baseline
评审任务：docs/status/reviews/TUP-20260810-role-b-review.md

先确认工作区干净并按评审文件中的命令检出远程评审源。比较 origin/main...HEAD，逐项阅读评审文件第 3 节列出的文档。优先找安全、权限、隐私、数据一致性、接口不可实现、推荐数据闭环和双人 AI 文件冲突风险。

不要初始化后端，不要改产品/架构规范，不要发起 GitHub 授权，不要创建 PR，不要 merge main。输出必须包含：阻塞问题、非阻塞问题、ADR-0001/0002/0003 结论、总体 Approved 或 Changes Requested、剩余风险和未执行检查。每个问题给出文件/行号、触发条件、影响和修复建议。

如需写文件，只填写本评审文件第 5 节；否则把第 5 节的完整 Markdown 原样发给角色 A，由角色 A 据实写入仓库。不能只回复“没问题”。
```

## 5. 角色 B 评审结论（待填写）

> Reviewer: 角色 B<br>
> Reviewed Commit: `TBD`<br>
> Reviewed At: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

### 5.1 阻塞问题

| ID | File / Line | Trigger | Impact | Required Fix |
| --- | --- | --- | --- | --- |
| B-001 | TBD | TBD | TBD | TBD |

没有阻塞问题时，将占位行替换为“无”，并说明仍存在的测试缺口或剩余风险。

### 5.2 非阻塞问题

| ID | File / Line | Observation | Suggested Follow-up |
| --- | --- | --- | --- |
| NB-001 | TBD | TBD | TBD |

### 5.3 ADR 结论

| ADR | Decision | Reason / Required Change |
| --- | --- | --- |
| ADR-0001 | `Accept / Keep Proposed / Changes Requested` | TBD |
| ADR-0002 | `Technically Approved / Changes Requested` | TBD |
| ADR-0003 | `Accept / Changes Requested` | TBD |

### 5.4 验证与剩余风险

- 实际执行的检查：TBD
- 未执行的检查及原因：TBD
- 剩余风险：TBD
- 允许集成到 `main`：`Yes / No`

## 6. 返回与落盘方式

角色 A 通过 QQ 发送远程分支名和本文件路径即可，不在 QQ 重复整份要求。角色 B 完成后采用其一：

1. 把第 5 节完整 Markdown 原样发给角色 A，角色 A 据实写回本文件并提交；
2. 在自己的评审分支中只修改本文件第 5 节，提交并推送后把分支名发给角色 A。

除本文件第 5 节外，角色 B 的评审 AI 不修改任何文件。需要修正规范时先写成阻塞/非阻塞问题，由对应负责人另开任务处理。
