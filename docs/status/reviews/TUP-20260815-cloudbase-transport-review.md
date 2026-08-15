# TUP-20260815 CloudBase 云托管传输技术验证评审

> Status: Proposed<br>
> Task Owner: 角色 A<br>
> Reviewer: 角色 B<br>
> Review State: Pending Role B Review<br>
> Last Updated: 2026-08-16

## 1. 评审范围

- `apps/miniapp/src/services/transport.ts` 的 `wx.cloud.callContainer` 边界、配置校验、错误映射和会话兼容；
- `services/api/Dockerfile`、`.dockerignore`、配置示例和 staging/production MySQL 强制规则；
- ADR-0006 官方可行性证据、计费边界和禁止部署边界；
- 个人主体类目限制与“社交-社区/论坛”候选结论是否需要补充合规意见。

## 2. 必查问题

- CloudBase 云托管是否应继续使用当前 `uni.login -> FastAPI jscode2session -> 平台 token` 流程，还是采用可信云托管身份头；任何认证变化必须另立 ADR；
- `wx.cloud.callContainer` 的路径、method、header、body 和错误响应是否与现有 API 契约兼容；
- 云托管服务端口、健康检查、非 root 用户、镜像基础版本和构建上下文是否符合 CloudBase 当前要求；
- MySQL VPC、迁移、连接池、备份恢复、密钥、日志、限流与回滚方案是否完整；
- CloudBase 当前实际套餐、免费额度、最小实例、休眠/缩容和欠费行为是否能满足角色 A 的成本要求。

## 3. 当前证据

| Check | Result | Notes |
| --- | --- | --- |
| 前端单元测试 | Passed | 6 个文件、33 项测试通过，含 CloudBase 成功、缺配置、非微信环境、网络失败与 401。 |
| 前端类型检查 | Passed | `vue-tsc --noEmit`。 |
| 微信构建 | Passed | fixture、HTTP API、CloudBase 三种构建通过。 |
| H5 API 构建 | Passed | HTTP API H5 构建通过；CloudBase 不用于 H5。 |
| 后端测试 / compileall | Passed with skips | 全量测试通过；7 项真实 MySQL 专项测试因未配置测试库跳过。 |
| Docker build | Not verified | 本机两次构建在基础镜像/依赖阶段长时间无输出并被终止；未获得成功镜像。 |
| CloudBase 控制台 / 真机 | Not run | 未创建或部署云托管服务，未产生付费资源。 |

## 4. 评审结论

`TBD`。角色 B 应填写 `Approved` 或 `Changes Requested`，并逐项说明部署、安全、数据库、微信登录和成本依据。在本文件结论为 `Approved` 且 ADR-0006 变为 `Accepted` 前，不得部署或将 CloudBase 设为默认生产传输。
