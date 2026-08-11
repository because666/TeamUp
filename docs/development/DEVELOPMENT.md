# TeamUp 开发指南

> Status: Proposed<br>
> Owner: 角色 A / 角色 B<br>
> Last Updated: 2026-08-11

## 1. 当前说明

微信小程序前端已在任务分支 `role-a/feature/TUP-20260811-frontend-foundation` 初始化，等待角色 B 评审和集成；后端工程仍未初始化。下方前端命令均已在 Windows、Node `v25.2.1`、npm `11.6.2` 上实际执行，团队长期使用的 Node LTS 版本仍需在 CI 或第二台开发机验证后确认。

## 2. 工具链登记

| 范围 | 工具 | 版本来源 | 安装命令 | 启动命令 | 测试命令 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 小程序 | UniApp `3.0.0-5020320260806002`、Vue `3.4.21`、TypeScript `4.9.5`、Vite `5.2.8` | `apps/miniapp/package-lock.json` | `cd apps/miniapp && npm ci` | `npm run dev:mp-weixin` | `npm test` | Ready for Review |
| 后端 | FastAPI 或 Spring Boot | ADR-0001 | `TBD` | `TBD` | `TBD` | TBD |
| 数据库 | MySQL | `TBD` | `TBD` | `TBD` | `TBD` | TBD |
| API 契约 | OpenAPI | 后端清单/生成配置 | `TBD` | `TBD` | `TBD` | Proposed |

版本必须由锁文件、wrapper 或明确的版本配置固定，不要只在聊天中约定。

### 2.1 微信小程序前端命令

所有命令在 `apps/miniapp/` 执行：

| 目的 | 命令 | 模式 / 产物 |
| --- | --- | --- |
| 按锁文件安装 | `npm ci` | 不写入真实密钥或 AppID |
| H5 合约模拟预览 | `npm run dev:h5` | `fixture`；仅用于页面开发和截图 |
| 微信合约模拟开发 | `npm run dev:mp-weixin` | `fixture`；导入 `dist/dev/mp-weixin` |
| H5 真实接口模式 | `npm run dev:h5:api` | API 未接入时明确返回 `BACKEND_NOT_CONFIGURED` |
| 微信真实接口模式 | `npm run dev:mp-weixin:api` | API 未接入时不模拟成功 |
| 类型检查 | `npm run type-check` | `vue-tsc --noEmit` |
| 单元测试 | `npm test` | Vitest；当前覆盖校验、fixture 来源和错误映射 |
| H5 演示构建 | `npm run build:demo:h5` | `fixture`，不得作为生产包 |
| 微信演示构建 | `npm run build:demo:mp-weixin` | `fixture`，导入 `dist/build/mp-weixin` |
| H5 生产检查 | `npm run build:h5` | 不启用 fixture |
| 微信生产检查 | `npm run build:mp-weixin` | 不启用 fixture；导入 `dist/build/mp-weixin` |

微信开发者工具中使用测试 AppID 或团队分配的开发 AppID；真实 AppID 不写入共享仓库。`manifest.json` 当前保持空 AppID，并关闭本地演示的 URL 校验，发布前必须由角色 B 按环境与域名白名单复核。

`@types/node` 固定为 `18.18.0` 以兼容模板使用的 TypeScript 4.9；`sass` 是 `uni-ui` 图标样式在微信端编译所需的显式依赖。升级 TypeScript、UniApp 或这两个依赖前必须重新运行全部构建目标。

## 3. 建议仓库布局

当前前端已采用下列布局；后端和共享契约目录仍须在对应技术决策确认后创建：

```text
apps/
  miniapp/            # 已初始化：UniApp 微信小程序；H5 仅作预览
services/
  api/                # 尚未创建：等待 ADR-0001
packages/
  contracts/          # 尚未创建：等待 OpenAPI 工具链
docs/
  ...
```

前端和后端目录创建后，各自放一份简短 `AGENTS.md`，记录该目录的真实命令、框架约束和测试要求。

## 4. 配置

- 仓库提供 `.env.example`，只放变量名和无敏感示例；
- 本地 `.env*`、证书、密钥和真实连接信息不得提交；
- 客户端只能包含可公开配置，微信密钥、数据库凭证和 AI Key 只能存在服务端；
- `local`、`test`、`staging`、`production` 使用独立凭证和数据；
- 新增配置时同步说明用途、是否必需、默认行为和安全级别。

## 5. 契约优先开发

跨角色功能按以下顺序推进：

1. 任务文件引用 PRD 需求 ID；
2. 双方确认 API 请求、响应、错误码和数据可见性；
3. 更新 OpenAPI/契约文档；
4. 角色 A 使用契约 mock 开发页面，角色 B实现接口；
5. 运行契约测试和联调；
6. 同步任务状态和验证证据。

Mock 必须与契约生成或受契约测试约束；禁止手写一套与真实接口逐渐漂移的数据结构。

## 6. 编码约定

- 命名清晰，避免不明缩写；领域词汇与 PRD/API 一致；
- 业务状态使用枚举或受控常量，不散落魔法字符串；
- 对外错误使用稳定错误码，内部异常不直接暴露给客户端；
- 时间以 UTC 存储，展示时由客户端按用户时区转换；
- 数据库写操作明确事务和幂等边界；
- 日志使用结构化字段和请求 ID，不记录令牌、密钥、私信正文和完整个人资料；
- 公共方法和复杂规则需要测试；注释只解释原因与约束。

格式和静态检查由各工程的自动化配置统一执行，不在不同 Codex 会话中发明不同风格。

## 7. 本地数据

- 只使用构造数据或匿名数据；禁止复制生产用户数据到本地；
- seed 数据应可重复生成，覆盖三类用户、不同项目阶段、技能组合、拉黑和邀请状态；
- 自动化测试不得依赖执行顺序或共享的长期测试账号；
- 上传文件使用专用测试存储或本地替代，不写入仓库。

## 8. 剩余开发环境工作

- 在 CI 或第二台开发机确认受支持的 Node LTS 版本；
- 前端分支集成后，从全新克隆再次执行 `npm ci` 和全部检查；
- 数据库创建和迁移命令；
- seed/reset 测试数据命令；
- 后端、契约和端到端测试命令；
- lint、格式化、类型检查和构建命令；
- 常见错误与解决方式。

所有命令必须在干净克隆中实际验证后才能写为可用。
