# TUP-20260810-docs-baseline

> Status: Ready for Review<br>
> Owner: 角色 A<br>
> Reviewer: 角色 B<br>
> Base Commit: `167edd5`<br>
> Branch: `role-a/docs/TUP-20260810-docs-baseline`<br>
> Last Updated: 2026-08-10

## 1. 目标

将两份原始 PDF 中的项目共识转为可开发、可验证的版本化文档，并建立两人分别使用 Codex 时必须遵守的范围、Git、状态、决策和交接机制。

## 2. 范围

- 根级 `AGENTS.md`、README、贡献与忽略规则；
- 产品、MVP、架构、API、数据、匹配、开发、测试、发布和安全文档；
- ADR 索引与三个初始决策；
- `CURRENT.md`、每任务状态文件和交接模板；
- 可选 GitHub PR 模板与 `.github` AI 规则；
- 规则算法冷启动、自训练轻量模型、数据闭环和模型发布规范。

## 3. 非目标

- 不初始化前端或后端工程；
- 不替角色 B 决定后端框架；
- 按用户授权提交并推送任务分支，但不直接合并 `main` 或部署；
- 不宣称未经验证的匹配权重、模型效果、数据门槛或性能指标已经确定。

## 4. 验收标准

- [x] 根 `AGENTS.md` 明确 AI 禁止事项、读文档顺序、职责和完成条件
- [x] 产品需求具有稳定 ID 和验收标准
- [x] 前后端具有 API、数据和匹配共享契约草案
- [x] 双人同步使用单负责人任务文件，避免共同状态文件高频冲突
- [x] 未决技术与产品事项进入 ADR
- [x] 文档内部相对链接全部有效
- [x] `AGENTS.md` 大小低于默认 32 KiB 限制
- [x] Git diff 和敏感信息检查完成
- [x] 明确规则算法 P0、自训练轻量模型 P1 和生成式 AI 的边界
- [x] 建立训练数据、评估、影子运行、模型登记和回退规范
- [ ] 角色 B 完成规则与技术可行性评审

## 5. 当前状态

角色 A 已确认自训练轻量推荐模型方向。文档、契约和校验已完成，远程任务分支已上传；角色 B 的核对范围和输出格式已写入独立评审文件，等待 QQ 通知后评审。

## 6. 验证记录

| Check | Result | Evidence |
| --- | --- | --- |
| 文件存在与 Git 状态 | Passed | 已检查根文件与 `docs/` 创建状态 |
| Markdown 相对链接 | Passed | 34 份 Markdown 的本地相对链接全部存在 |
| AGENTS 指令大小 | Passed | root + docs 为 8,769 bytes；root + .github 为 8,340 bytes，低于 32,768 bytes |
| 敏感信息扫描 | Passed | 常见 API Key、云密钥、私钥和赋值模式无命中 |
| Git diff 检查 | Passed | 无 whitespace error；当前位于规范任务分支 |
| 推荐术语一致性 | Passed | 无旧 `ruleVersion`、大模型打分或未决 AI 范围表述残留 |
| PR 可选流程一致性 | Passed | 旧“必须 PR”表述已替换；QQ 仅通知、仓库评审文件为集成依据 |
| 远程同步 | Passed | [任务分支](https://github.com/because666/TeamUp/tree/role-a/docs/TUP-20260810-docs-baseline) 已建立并配置 upstream |

## 7. 待评审重点

- 角色 B 评审推荐事件、特征 schema、训练/推理方案和数据安全；
- 匹配 V0.1 权重、资料缺失和低置信度处理；
- Git 同步、文件评审和集成顺序是否符合双方习惯；
- 安全治理功能是否纳入 P0；
- 文档状态从 Proposed 转为 Confirmed/Accepted 的批准方式。

## 8. 下一步

角色 A 通过 QQ 通知角色 B 按 [评审任务](../reviews/TUP-20260810-role-b-review.md) 核对。角色 B 的结论必须写入该文件或以可原样落盘的 Markdown 返回；批准后再集成到 `main`，无需创建 Pull Request。
