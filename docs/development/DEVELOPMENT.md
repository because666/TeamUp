# TeamUp 开发指南

> Status: Proposed<br>
> Owner: 角色 A / 角色 B<br>
> Last Updated: 2026-08-16

## 1. 当前说明

微信小程序前端已在 `apps/miniapp` 初始化并提供 fixture 与真实 API 两种模式；FastAPI 后端已在 `services/api` 初始化，包含内存/MySQL 存储、Alembic 迁移和 OpenAPI。两端当前组合在独立集成任务分支，尚未合入 `main`。下方命令均来自工程清单并已在任务分支执行；Node LTS、真实微信环境、测试 MySQL 和生产部署仍须在对应环境复验。

## 2. 工具链登记

| 范围 | 工具 | 版本来源 | 安装命令 | 启动命令 | 测试命令 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 小程序 | UniApp `3.0.0-5020320260806002`、Vue `3.4.21`、TypeScript `4.9.5`、Vite `5.2.8` | `apps/miniapp/package-lock.json` | `cd apps/miniapp && npm ci` | `npm run dev:mp-weixin` | `npm test` | Ready for Review |
| 后端 | FastAPI | `services/api/pyproject.toml` | `python -m pip install -e ".[test]"` | `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` | `python -m pytest` | Confirmed |
| 数据库 | MySQL 8.0/8.4、SQLAlchemy、Alembic、PyMySQL | `ADR-0004`、`services/api/pyproject.toml` | 随后端依赖安装；MySQL 服务安装方式按环境确定 | `python -m alembic upgrade head` | `TEAMUP_TEST_MYSQL_URL` 配置后运行 `python -m pytest` | Confirmed |
| API 契约 | FastAPI OpenAPI | `services/api/app/main.py`、契约测试 | 随后端依赖安装 | 启动后访问 `/openapi.json` | `python -m pytest` | Ready for Review |

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
| 微信 CloudBase 技术验证 | `npm run dev:mp-weixin:cloudbase` | 使用本地未提交的 CloudBase 环境与服务配置 |
| 类型检查 | `npm run type-check` | `vue-tsc --noEmit` |
| 单元测试 | `npm test` | Vitest；当前覆盖校验、fixture 来源和错误映射 |
| H5 演示构建 | `npm run build:demo:h5` | `fixture`，不得作为生产包 |
| 微信演示构建 | `npm run build:demo:mp-weixin` | `fixture`，导入 `dist/build/mp-weixin` |
| H5 生产检查 | `npm run build:h5` | 不启用 fixture |
| 微信生产检查 | `npm run build:mp-weixin` | 不启用 fixture；导入 `dist/build/mp-weixin` |
| 微信 CloudBase 构建检查 | `npm run build:mp-weixin:cloudbase` | 非默认技术验证；导入 `dist/build/mp-weixin` |

微信开发者工具中使用测试 AppID 或团队分配的开发 AppID；真实 AppID 不写入共享仓库。`manifest.json` 当前保持空 AppID，并关闭本地演示的 URL 校验，发布前必须由角色 B 按环境与域名白名单复核。

`@types/node` 固定为 `18.18.0` 以兼容模板使用的 TypeScript 4.9；`sass` 是 `uni-ui` 图标样式在微信端编译所需的显式依赖。升级 TypeScript、UniApp 或这两个依赖前必须重新运行全部构建目标。

## 3. 建议仓库布局

当前前后端已采用下列布局；共享契约生成目录仍须在工具链决策后创建：

```text
apps/
  miniapp/            # 已初始化：UniApp 微信小程序；H5 仅作预览
services/
  api/                # 已初始化：FastAPI、MySQL 适配器与 Alembic
packages/
  contracts/          # 尚未创建：等待共享 OpenAPI 生成工具链
docs/
  ...
```

前端和后端目录创建后，各自放一份简短 `AGENTS.md`，记录该目录的真实命令、框架约束和测试要求。

## 4. 配置

### 4.1 前端 API 模式

- `apps/miniapp/.env.example` 中的 `VITE_API_BASE_URL` 必须包含 `/api/v1` 前缀，例如本地 `http://127.0.0.1:8000/api/v1`；
- 非本地地址只允许 HTTPS，本地 HTTP 只接受 `localhost` 或 `127.0.0.1`；
- 微信小程序 API 模式使用 `npm run dev:mp-weixin:api`，登录时通过 `uni.login({ provider: "weixin" })` 获取一次性 code，再交给后端换取平台会话；
- H5 API 模式可验证无登录接口和错误状态，但不能替代微信 code 流程，无法调用微信登录时必须显式失败；
- 微信开发者工具和小程序后台必须把 API 域名配置为 request 合法域名，开发/生产 AppID、微信密钥和平台签名密钥不得写入前端环境文件；
- access token 仅由 services 层读取并放入 `Authorization: Bearer`，页面不得解析 token；成功退出后清理本地平台会话。

### 4.2 CloudBase 技术验证模式

- `cloudbase` 构建模式继续调用现有 `/api/v1` FastAPI 契约，只将传输从 `uni.request` 切换为 `wx.cloud.callContainer`；
- 本地未提交配置必须提供 `VITE_CLOUDBASE_ENV_ID` 和 `VITE_CLOUDBASE_SERVICE`，`VITE_CLOUDBASE_API_PREFIX` 默认 `/api/v1`；
- 环境 ID 与服务名属于客户端可见配置，不是密钥，但仍按环境注入，避免把开发/生产资源混用；
- AppSecret、数据库连接串和平台签名密钥仍只能放在云托管服务端配置中；
- 页面不得直接调用 `wx.cloud.callContainer` 或云数据库，所有调用继续经过 `src/services/`；
- CloudBase 模式缺少配置或运行在非微信环境时必须显式失败，不回退 fixture 或伪造成功；
- 本模式是 ADR-0006 的技术验证，不代表已批准部署、付费或正式切换运行拓扑。

### 4.3 共享配置边界

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
- 从全新克隆再次执行两端安装、测试和构建；
- 在隔离测试 MySQL 上执行全部迁移与集成测试；
- 确认 OpenAPI 到前端类型的共享生成工具链；
- 补齐 seed/reset 测试数据、端到端联调和 staging 命令；
- 补齐生产部署、备份恢复、监控和回滚命令；
- 常见错误与解决方式。

所有命令必须在干净克隆中实际验证后才能写为可用。

## 9. FastAPI 后端基础实现

可运行后端位于 `services/api`。`local` 和 `test` 可显式使用内存存储；MySQL 适配器与 Alembic 迁移已实现，`staging` 和 `production` 禁止使用内存存储。

在 `services/api` 目录执行：

```powershell
python -m pip install -e ".[test]"
$env:TEAMUP_ENVIRONMENT = "local"
$env:TEAMUP_ALLOW_LOCAL_LOGIN = "true"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

在 `services/api` 目录执行检查：

```powershell
python -m pytest
python -m compileall -q app tests
python -m pip check
```

本地登录约定：调用 `POST /api/v1/auth/wechat/login` 时，`code` 使用 `local:<subject>`，并将 `consentAccepted` 设为 `true`。当 `TEAMUP_ENVIRONMENT=production` 时，该替代方案自动禁用。代理端口 `7897` 仅用于网络访问，不作为服务监听端口。

真实微信登录配置：在服务端环境设置 `TEAMUP_WECHAT_APP_ID`、`TEAMUP_WECHAT_APP_SECRET`，可选设置 `TEAMUP_WECHAT_SESSION_ENDPOINT`、`TEAMUP_WECHAT_TIMEOUT_SECONDS` 和 `TEAMUP_WECHAT_PROXY_URL`。本机需要通过 7897 出网时，将后者设为 `http://127.0.0.1:7897`；服务仍监听 8000。禁止将 secret 写入前端、仓库、日志或响应。真实微信 code 只能使用一次；本地测试使用 `local:<subject>`，不会调用微信。

## 10. MySQL 持久化与迁移

服务端配置：

```powershell
$env:TEAMUP_ENVIRONMENT = "local"
$env:TEAMUP_STORE_BACKEND = "mysql"
$env:TEAMUP_DATABASE_URL = "mysql+pymysql://<user>:<password>@<host>:3306/<database>?charset=utf8mb4"
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

连接串只允许存在于服务端环境或密钥服务，不得提交、打印或传给前端。迁移前确认目标数据库和备份策略；`downgrade base` 只用于一次性测试数据库的回滚演练，不作为生产数据恢复方式。

真实 MySQL 集成测试需要先对测试库执行 `python -m alembic upgrade head`，然后显式提供独立测试连接串：

```powershell
$env:TEAMUP_TEST_MYSQL_URL = "mysql+pymysql://<test-user>:<test-password>@<host>:3306/<test-database>?charset=utf8mb4"
python -m pytest -ra
```

未配置 `TEAMUP_TEST_MYSQL_URL` 时，MySQL 专属测试会显示为 skipped；SQLite 仓储与迁移测试仍会执行，但不能替代真实 MySQL 验证。

## 11. CloudBase FastAPI 容器技术验证

`services/api/Dockerfile` 只用于本地构建和 CloudBase 云托管可行性评审。它继续启动 `app.main:app`，监听容器端口 80，并以 `/api/v1/health/ready` 作为容器健康检查。

在 `services/api` 执行本地构建：

```powershell
docker build -t teamup-api:cloudbase-spike .
```

CloudBase staging/production 必须至少配置：

- `TEAMUP_ENVIRONMENT=staging|production`；
- `TEAMUP_STORE_BACKEND=mysql`；
- 服务端 MySQL 连接串和微信 AppID/AppSecret；
- 关闭本地替代登录。

示例变量名见 `services/api/cloudbase.env.example`，其中所有值均为占位符。应用会拒绝 staging/production 使用内存存储。数据库迁移必须作为独立受控步骤执行，不在每个容器实例启动时自动运行。

当前只允许本地镜像构建和启动检查。镜像推送、CloudBase 服务创建、MySQL 初始化、环境变量录入、流量开放和付费资源启用仍需 ADR-0006 接受、Role B 评审和当前用户明确授权。
