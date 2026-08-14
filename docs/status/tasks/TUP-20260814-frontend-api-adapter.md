# TUP-20260814 前端真实 API 适配层

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Base Commit: `6dbd568ddb8472cf94058a2372b0d7eeb2498fb5`  
> Branch: `role-b/feature/TUP-20260814-frontend-api-adapter`  
> Last Updated: 2026-08-14

## 1. 目标

在前端 foundation 的 services 边界内接入后端已推送契约，完成 API 模式下的微信登录、会话凭证、名片读写、我的项目读取、项目草稿保存和发布动作；fixture 模式继续保持独立，不伪造真实服务成功。

## 2. 范围

- `apps/miniapp/src/services/repository.ts`：统一 HTTP 请求、响应 envelope、错误映射和 P0 repository 方法；
- `apps/miniapp/src/services/runtime.ts` 与 `storage.ts`：API base URL、会话凭证和退出清理；
- `apps/miniapp/src/domain/models.ts`：补充 API 模式返回所需的非敏感 session 元数据类型；
- API 模式登录 -> 名片 -> 我的项目 -> 草稿 -> 发布流程；
- 前端单元测试和开发文档中的 API 模式配置说明。

## 3. 非目标

- 不修改后端 API、数据库、认证算法或微信服务端密钥；
- 不把 access token、微信 code 或响应正文写入日志；
- 不在 fixture 模式调用网络；
- 不实现匹配、消息、邀请和举报页面的真实适配，它们保留后续任务边界。

## 4. 跨角色协作记录

- 修改方：角色 B（跨职责实现，经用户明确授权）；
- 评审方：角色 A；
- 接口基线：后端 `role-b/feature/TUP-20260813-ci-contract-gate` 的 API contract 与 `f053007`；
- 影响范围：前端 services 适配层、会话存储、P0 登录/名片/项目页面的网络行为；
- 角色 A 需要重点复核：微信登录调用方式、字段映射、错误状态展示和 fixture/API 模式切换。

## 5. 验收标准

- API 模式请求统一使用 `VITE_API_BASE_URL`，成功响应读取 `data`，保留服务端 `requestId`；
- 401/403/409/422、网络失败和无配置状态映射为现有 `AppServiceError`，不泄漏服务端内部文本；
- 登录成功后只保存必要的短期 access token 和 userId，退出时清理；
- API 模式不会落入 fixture storage，也不会在未获得微信 code 时伪造登录成功；
- 项目新建使用 POST，已有项目使用微信原生支持的 PUT 兼容路由，发布使用版本号并支持 409 冲突提示；
- fixture 测试、API adapter 单元测试、类型检查和 H5/微信小程序构建通过。

## 6. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `npm install --package-lock=false --registry=https://registry.npmjs.org --replace-registry-host=always` | Passed | 使用 `7897` 代理安装 588 个包，未修改 lockfile；直接 `npm ci` 因 lockfile 内 npmmirror 下载地址连接重置失败 |
| `npm test` | Passed | 4 个测试文件、17 项测试通过；新增 5 项 API adapter 测试 |
| `npm run type-check` | Passed | `vue-tsc --noEmit` |
| `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run build:h5` | Passed | API 模式 H5 构建通过 |
| `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run build:mp-weixin` | Passed | API 模式微信小程序构建通过 |
| 敏感信息与生成物检查 | Passed | 未创建 `.env`；`node_modules`/`dist` 均被忽略；未发现密钥或真实 token |

## 7. 剩余风险

- 当前仓库没有真实微信 AppID、后端 staging 地址或微信开发者工具，真实平台登录和真机网络仍需环境具备后验证；
- access token 的生产刷新/轮换策略仍由后端会话契约决定，本任务只实现已有 accessToken 的短期客户端保存和清理。
- 微信客户端不支持 PATCH；本任务改用 PUT，后端等价兼容路由由 `TUP-20260814-project-put-compat` 独立任务提供。
