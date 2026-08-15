# TUP-20260815：CloudBase 云托管传输技术验证

> Status: In Progress<br>
> Owner: 角色 A（前端与产品）<br>
> Reviewer: 角色 B（后端、部署与安全）<br>
> Base Commit: `b4f5c82ad00918e9b0b9aca1918a7be6940246be`<br>
> Branch: `role-a/feature/TUP-20260815-cloudbase-transport`<br>
> Last Updated: 2026-08-16

## 1. 目标

在不改变默认运行方式、不部署付费资源的前提下，验证微信小程序通过 `wx.cloud.callContainer` 调用 CloudBase 云托管 FastAPI 的代码路径，并为现有 FastAPI 服务提供可复现的容器构建入口。

## 2. 依据

- PRD：P0 已确认能力保持不变；本任务不新增产品功能。
- API：继续使用现有 `/api/v1` 契约，不改变 DTO、错误码或鉴权语义。
- ADR：[ADR-0001](../../decisions/ADR-0001-backend-framework.md)、[ADR-0004](../../decisions/ADR-0004-mysql-data-access.md)、[ADR-0006](../../decisions/ADR-0006-cloudbase-runtime-evaluation.md)。
- 微信发布准备：[WECHAT_RELEASE_READINESS.md](../../product/WECHAT_RELEASE_READINESS.md)。

## 3. 范围

- 在 `apps/miniapp/src/services/` 增加 HTTP/CloudBase 可选传输边界，页面与 repository 业务映射不感知传输方式；
- 使用公开、非敏感的构建变量配置 CloudBase 环境 ID、服务名和 API 前缀；
- 为 CloudBase 请求映射、缺失配置、网络失败、401 会话清理增加测试；
- 为 `services/api` 增加最小容器构建文件，继续运行现有 FastAPI 应用和 `/api/v1` 健康检查；
- 同步开发命令、配置边界、官方依据和 Role B 评审事项。

角色 A 实现前端传输和容器验证材料；角色 B 必须复核容器、MySQL、微信登录、密钥、计费、部署和安全边界。

## 4. 非目标

- 不创建或部署 CloudBase 服务，不初始化 MySQL，不购买套餐或产生云资源；
- 不提交真实 AppID、环境 ID、服务名、数据库连接串、AppSecret 或平台签名密钥；
- 不将 CloudBase 设为默认或生产运行方式；
- 不使用云数据库替代 MySQL，不把 FastAPI 改写为云函数；
- 不改变公共 API、数据表、鉴权模型、产品功能或服务类目结论；
- 不把微信开发者工具模拟器验证表述为真机或线上验收。

## 5. 依赖与假设

- CloudBase 官方文档当前说明云托管支持 FastAPI、MySQL 集成和 `wx.cloud.callContainer`；真实套餐、地域与控制台能力以创建环境时显示为准；
- `wx.cloud.callContainer` 只在微信小程序环境可用，H5 继续使用 fixture 或 HTTP API；
- 真实 CloudBase 环境与服务名由本地未提交配置注入；缺失时必须显式失败；
- 技术验证不代表 ADR-0006 已接受，也不授权部署。

## 6. 计划

- [x] 核对 CloudBase FastAPI、MySQL、小程序调用和计费官方文档。
- [x] 建立 CloudBase 可选传输边界和配置校验。
- [x] 增加传输单元测试和微信构建命令。
- [x] 增加 FastAPI 容器构建文件和持久环境配置保护。
- [x] 更新开发、发布准备、ADR、评审文件和验证记录。
- [ ] 在可用 Docker 网络环境完成镜像构建/启动，并在真实 CloudBase 开发环境完成联调。

## 7. 验收标准

- [x] 默认 fixture 与 HTTP API 行为和现有测试保持不变。
- [x] CloudBase 模式使用 `/api/v1` 路径、`X-WX-SERVICE` 和现有 bearer token，不向页面暴露传输细节。
- [x] 缺少 CloudBase 环境或服务配置、非微信环境、网络失败和 401 均返回稳定错误并正确处理会话。
- [ ] FastAPI 容器监听 `0.0.0.0:80`，不使用内存存储作为 staging/production 默认值（配置保护已测试，镜像启动未验证）。
- [x] 前端测试、类型检查、fixture/HTTP/CloudBase 微信构建和后端测试实际通过。
- [x] 未部署、未付费、未提交任何真实环境配置或密钥。

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-15 | 创建技术验证任务 | 角色 A 要求控制早期服务器/域名成本，同时明确保留 FastAPI。 |
| 2026-08-15 | 将 CloudBase 限定为非默认技术验证 | ADR-0006 尚未由角色 B 接受，禁止把验证代码当作生产部署决定。 |
| 2026-08-16 | 完成本地适配与自动化验证 | 前端传输、构建、后端配置保护均通过；Docker 镜像和真实环境仍待验证。 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| CloudBase 官方文档核对 | Passed | 已核对 FastAPI、MySQL、小程序调用与计费页面；链接见 ADR-0006。 |
| `npm test` | Passed | 6 个文件、33 项测试通过。 |
| `npm run type-check` | Passed | 无 TypeScript 错误。 |
| 微信 / H5 构建 | Passed | fixture、HTTP API、CloudBase 微信构建及 HTTP API H5 构建通过。 |
| 后端 `pytest -q` / `compileall` | Passed with skips | 全量测试通过；7 项真实 MySQL 专项测试未配置而跳过。 |
| `docker build -t teamup-api:cloudbase-spike .` | Not verified | 本机两次构建长时间停在基础镜像/依赖阶段并被终止，未生成镜像。 |
| CloudBase 控制台 / 真机 | Not run | 尚未获得开发环境与服务；本任务不创建付费资源。 |

## 10. 当前状态与下一步

- 最后完成：非默认 CloudBase 传输、FastAPI 容器材料、类目说明、自动化测试和三种微信构建。
- 当前阻塞：本机 Docker 构建未完成；真实 CloudBase 环境、计费方案和部署仍需角色 B 与角色 A 共同确认。
- 下一步：角色 A 在微信开发者工具创建开发环境并提供环境/套餐页面；角色 B 评审后完成镜像与 MySQL 联调。
- 最后相关提交：`e3bb364`。
