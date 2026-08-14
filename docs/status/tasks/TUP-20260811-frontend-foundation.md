# TUP-20260811-frontend-foundation：前端工程与 P0 页面骨架

> Status: Ready for Review<br>
> Owner: 角色 A<br>
> Reviewer: 角色 B（契约使用与安全边界）<br>
> Base Commit: `10c395e`<br>
> Branch: `role-a/feature/TUP-20260811-frontend-foundation`<br>
> Last Updated: 2026-08-11

## 1. 目标

建立可运行、可测试的 UniApp 微信小程序前端工程，并用明确标注的合约 fixture 跑通“登录 -> 能力名片 -> 项目草稿/岗位 -> 发布预览 -> 发布结果”的 P0 页面与状态路径，为后端 OpenAPI 完成后的真实联调保留单一适配入口。

## 2. 依据

- PRD：`AUTH-001`、`PROF-001/002`、`PROJ-001`
- 产品：[用户流程](../../product/USER_FLOWS.md)、[信息架构](../../product/INFORMATION_ARCHITECTURE.md)、[页面规范](../../product/SCREEN_SPEC.md)
- API：[API_CONTRACT.md](../../architecture/API_CONTRACT.md)
- 安全：[SECURITY_AND_PRIVACY.md](../../security/SECURITY_AND_PRIVACY.md)

## 3. 范围与交付物

- 使用官方 UniApp Vue 3 + TypeScript + Vite 模板初始化 `apps/miniapp/`；
- 固定实际验证过的 Node、包管理器、依赖、启动、测试、类型检查和构建命令；
- 增加 `apps/miniapp/AGENTS.md`，只记录该技术栈的边界和真实命令；
- 建立发现、匹配、消息、我的一级框架和 P0 切片页面；
- 建立统一页面状态、表单校验、非敏感本地草稿与请求适配边界；
- 使用带 `fixture_`、`PROPOSED_GAP` 和 `GAP-*` 来源的合约 mock；
- 覆盖正常、loading、empty、validation、network、401、403、409、重复提交和发布恢复状态；
- 运行 H5 和微信小程序构建，并对移动端 H5 做截图核对。

## 4. 非目标

- 不实现或模拟真实微信身份交换、平台 token 签发和服务端权限成功；
- 不新增、删除或确认公共 API DTO、数据库 schema、认证授权或隐私规则；
- 不初始化后端、数据库、OpenAPI 生成或部署环境；
- 不实现匹配算法、消息、邀请和运营后台的完整业务；
- 不把 mock 成功响应表述为后端已完成或联调通过；
- 未经另行授权不 commit、push、merge 或部署。

## 5. 依赖与假设

- 用户已于 2026-08-11 批准开始前端工作，并接受上一轮建议的 UniApp + Vue 3 + TypeScript + Vite 方向。
- API/数据仍为 `Proposed`；真实客户端类型必须等待 OpenAPI，当前 fixture 只服务页面开发。
- 同伴的前后端对接指南位于远程分支 `origin/role-a/docs/TUP-20260810-role-a-product-backend`，尚未评审集成；本任务只采用其与现有仓库规则一致的部分。
- 当前已在 Windows、Node `v25.2.1`、npm `11.6.2` 上验证；团队长期 Node LTS 版本仍待 CI 或第二台开发机确认。

## 6. 计划

- [x] 研究同类产品与移动端交互参考，确定单一视觉方向
- [x] 核对官方 UniApp 模板和依赖版本，初始化工程
- [x] 建立前端目录规则、设计 token、基础组件和状态模型
- [x] 实现 P0 页面与 fixture/mock 适配层
- [x] 增加表单、状态转换和 mock 安全边界测试
- [x] 运行类型检查、测试、H5 与微信小程序构建
- [x] 使用移动端截图核对布局、状态和交互
- [x] 更新开发指南、任务状态和剩余契约缺口

## 7. 验收标准

- [x] 从干净安装可执行登记的前端命令
- [x] P0 页面可以在不调用真实后端的情况下完整演示，且持续显示 mock 环境标识
- [x] 任何 fixture 均不含 token、微信 code、真实身份或个人隐私数据
- [x] 表单校验、未保存退出、重复提交、401/403/409 和网络失败有明确状态
- [x] 页面不直接拼 API URL、解析 token 或判断服务端资源权限
- [x] H5 和微信小程序构建通过；测试和类型检查通过
- [x] 移动端无重叠、裁切、横向溢出或不可点击控件
- [x] 文档、任务状态、契约缺口和实际验证证据同步

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-11 | 创建任务并开始实施 | 后端尚未初始化，角色 A 可依据产品规范并行完成前端与合约 mock |
| 2026-08-11 | 初始化 UniApp 微信小程序并完成 P0 页面链路 | 后端尚未开工，先用来源明确的 fixture 验证产品流程 |
| 2026-08-11 | 仅保留 H5 预览与微信小程序平台依赖 | 当前产品目标为微信小程序，减少无关构建面与依赖 |
| 2026-08-11 | 建立角色 B 独立评审文件 | 集成前需核对契约使用、安全边界和微信端行为 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `npm ci` | Passed | 从 `package-lock.json` 重装 638 个包；只有上游 deprecated 警告，无安装失败 |
| `npm run type-check` | Passed | `vue-tsc --noEmit` |
| `npm test` | Passed | 3 个测试文件、12 个测试通过；覆盖字段校验、fixture 来源和 401/403/409 等错误映射 |
| `npm run build:demo:h5` | Passed | fixture 演示构建 |
| `npm run build:h5` | Passed | API 模式生产检查；未配置后端时不模拟成功 |
| `npm run build:demo:mp-weixin` | Passed | fixture 微信小程序构建；产物 `dist/build/mp-weixin` |
| `npm run build:mp-weixin` | Passed | API 模式微信小程序构建 |
| H5 页面矩阵 | Passed | Playwright 检查 10 个页面，移动端 `390x844` 无横向溢出；补查最后项目卡滚动后不被底栏遮挡 |
| H5 完整流程 | Passed | 登录、名片校验/保存、项目校验、保存预览、确认发布、`PUBLISHED` 结果均实际操作通过 |
| H5 未保存退出 | Passed | 单页栈下名片确认弹窗与项目三选项 action sheet 均出现，继续编辑保持当前页面 |
| 桌面补充检查 | Passed | `1440x900` 检查发现页和项目编辑页，无横向溢出；H5 只作为开发预览 |
| `npm audit --omit=dev --audit-level=high` | Not run | 当前 `npmmirror` 不实现 audit API；改用官方 npm registry 后 120 秒超时，不能据此声明无漏洞 |
| 微信开发者工具 / 真机 | Not run | 当前会话无团队 AppID 与开发者工具自动化；需角色 B 或集成前人工导入产物检查 |

## 10. 当前状态与下一步

- 最后完成：微信小程序 P0 fixture 链路、状态处理、测试、四类构建、视觉检查、开发指南和评审入口已完成。
- 当前阻塞：实现本身无阻塞；真实微信登录/API 联调等待角色 B 的 OpenAPI/DTO 与 `GAP-*` 结论。
- 下一步：本分支推送后通过 QQ 通知角色 B 按 [评审文件](../reviews/TUP-20260811-frontend-foundation-review.md) 核对；评审通过前不集成 `main`。
- 最后相关提交：以远程分支 `role-a/feature/TUP-20260811-frontend-foundation` 的 HEAD 为准；任务基线为 `10c395e`。
