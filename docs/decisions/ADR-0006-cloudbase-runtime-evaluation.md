# ADR-0006: CloudBase 低成本运行方案评估

> Status: Proposed<br>
> Decision Owner: 角色 B<br>
> Product Requester: 角色 A<br>
> Reviewers: 角色 A / 角色 B<br>
> Date: 2026-08-15

## Context

角色 A 希望在尚未验证需求和用户量前，避免先购买独立服务器、域名和长期数据库资源，并已在微信开发者工具中准备创建云开发环境。现有仓库已通过 ADR-0001 确认 FastAPI，通过 ADR-0004 确认 MySQL、SQLAlchemy 和 Alembic。部署平台方向为腾讯云，但具体生产拓扑仍为 `TBD`。

“开启微信云开发”只会创建微信侧的云环境；它不会自动部署 FastAPI、迁移 MySQL 数据、配置微信登录密钥或让真机访问本地 `127.0.0.1`。将云数据库或云函数直接作为权威后端，会改变已接受的 FastAPI/MySQL 决策，因此不得在未确认本 ADR 前实施。

## Decision Drivers

- 在小程序早期验证阶段控制固定成本；
- 保留已实现并已测试的 FastAPI、MySQL、Alembic 和 API 契约；
- 不让小程序客户端直接拥有数据库写权限；
- 保证微信登录、资源级授权、联系信息保护、备份和数据迁移可以审查；
- 为未来使用自有 HTTPS 域名和服务器保留可逆路径。

## Options

### Option A: CloudBase 云函数与云数据库直接承载 P0

- 优点：可以较低门槛开始微信生态内测试，客户端可通过云调用访问业务能力。
- 缺点：需要把 FastAPI 接口和 MySQL 持久化逻辑迁移或重写为云函数与云数据库实现。
- 风险：会改变 ADR-0001、ADR-0004 的关键技术结论；若客户端直连数据库，会绕过服务端鉴权、审计和隐私边界。

### Option B: CloudBase 云托管运行 FastAPI，并继续使用受管理的 MySQL

- 优点：保留现有 FastAPI、OpenAPI、SQLAlchemy 和 Alembic；后续可迁移到自建服务器和 HTTPS 域名。
- 缺点：云托管与数据库资源仍可能按量或按套餐产生费用；需要 Role B 验证容器运行、网络、密钥、健康检查、MySQL 连通性、备份和微信调用方式。
- 风险：不能仅凭开发者工具的“云开发”选项假定已部署成功或成本为零。

### Option C: 保持本地开发，需求验证后再部署 FastAPI

- 优点：不新增云资源，也不改变当前代码。
- 缺点：只能使用 fixture/H5 或开发工具模拟器验证；手机无法访问本机服务，无法完成真实微信登录和多用户联调。
- 风险：把本地演示误认为可上线服务，延后真实网络、数据库、备份和安全问题的发现。

## Decision

`TBD`。当前已确认的临时边界如下：

- FastAPI、MySQL、SQLAlchemy、Alembic 和现有 API 契约必须保留，不删除、不降级、不迁移生产数据；
- 角色 A 可以创建一个微信云开发环境，用于了解控制台能力和小程序工具链；创建时不得购买套餐、开通付费资源或写入真实密钥；
- 在角色 B 完成 Option B 的技术与成本核验前，CloudBase 环境不得被声明为 P0 生产后端，客户端不得直连云数据库；
- 任何云函数/云数据库重写、公开部署、域名配置、真实微信凭证配置、数据库迁移或付费资源启用都需要独立任务、Role B 评审和本 ADR 变为 `Accepted`。

## Feasibility Evidence

CloudBase 官方文档于 2026-08-15 核对结果：

- [FastAPI](https://docs.cloudbase.net/run/develop/languages-frameworks/fastapi)：云托管支持以容器方式部署 FastAPI，示例监听 `0.0.0.0:80`；
- [微信小程序调用云托管](https://docs.cloudbase.net/run/develop/access/mini)：已关联环境的小程序可使用 `wx.cloud.callContainer`，仅由小程序调用时无需配置服务器域名；
- [MySQL 数据库集成](https://docs.cloudbase.net/run/develop/resource-integration/mysql)：云托管可以通过内网连接云开发或腾讯云 MySQL，也可连接公网 MySQL；生产建议内网；
- [计费相关](https://docs.cloudbase.net/run/faq/fee)：云托管按实例 CPU 与内存使用计量，微信云托管按日结算，云开发中的云托管按环境套餐、资源包和按量方式扣量。

上述证据证明 Option B 技术上可继续验证，但不能证明具体账号存在免费额度，也不构成成本或生产部署批准。

## Consequences

- 正面影响：可以继续完成小程序后台基础信息、头像、开发者成员和开发工具导入，同时不牺牲已有后端投入。
- 负面影响：真实微信登录、真机 API、持久化数据和多人联调仍处于 `TBD`，不能把 fixture 演示当作生产可用。
- 后续任务：Role B 对 Option B 完成可行性、当前计费规则、最小配置、MySQL 备份恢复、密钥管理、微信登录、域名需求和回滚方案的核验；角色 A 验收成本、用户流程和小程序端调用体验。
- 回退/复审条件：若 CloudBase 云托管不能以可接受成本运行 FastAPI/MySQL，保留 Option C，待预算允许时采用独立腾讯云部署；若双方选择 Option A，必须通过新的 ADR 明确替代 ADR-0001 和 ADR-0004 的部分结论并先迁移契约与安全测试。
