# TeamUp 开发指南

> Status: Proposed<br>
> Owner: 角色 A / 角色 B<br>
> Last Updated: 2026-08-11

## 9. FastAPI 后端基础实现

可运行后端位于 `services/api`。当前仅在 `local` 和 `test` 使用明确标注的内存存储；MySQL 适配器和迁移属于后续独立任务。

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
```

本地登录约定：调用 `POST /api/v1/auth/wechat/login` 时，`code` 使用 `local:<subject>`，并将 `consentAccepted` 设为 `true`。当 `TEAMUP_ENVIRONMENT=production` 时，该替代方案自动禁用。代理端口 `7897` 仅用于网络访问，不作为服务监听端口。

## 1. 当前说明

后端工程已在 `services/api` 初始化并完成首条纵向验证；前端工程位于角色 A 的独立分支。后端基础命令已在本文件第 9 节记录，未实现的前端、MySQL 和完整生产部署命令仍保持 `TBD`，不得据此推断为已完成。

## 2. 工具链登记

| 范围 | 工具 | 版本来源 | 安装命令 | 启动命令 | 测试命令 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 小程序 | UniApp | `TBD` | `TBD` | `TBD` | `TBD` | TBD |
| 后端 | FastAPI | `services/api/pyproject.toml` | `python -m pip install -e ".[test]"` | `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` | `python -m pytest` | Confirmed |
| 数据库 | MySQL | `TBD` | `TBD` | `TBD` | `TBD` | TBD |
| API 契约 | OpenAPI | 后端清单/生成配置 | `TBD` | `TBD` | `TBD` | Proposed |

版本必须由锁文件、wrapper 或明确的版本配置固定，不要只在聊天中约定。

## 3. 建议仓库布局

布局需在技术栈确认后创建，不要为占位提前生成空工程：

```text
apps/
  miniapp/            # UniApp 微信小程序
services/
  api/                # 后端应用
packages/
  contracts/          # OpenAPI 生成类型或共享契约（若工具链支持）
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

## 8. 完成开发环境初始化时必须补充

- 受支持的操作系统与运行时版本；
- 一条从全新克隆到启动成功的路径；
- 数据库创建和迁移命令；
- seed/reset 测试数据命令；
- 前端、后端、契约、端到端测试命令；
- lint、格式化、类型检查和构建命令；
- 常见错误与解决方式。

所有命令必须在干净克隆中实际验证后才能写为可用。
