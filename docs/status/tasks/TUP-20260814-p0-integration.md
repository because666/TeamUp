# TUP-20260814 P0 前后端集成

> Status: In Progress  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Base Commit: `1bc3cfa`  
> Branch: `role-b/feature/TUP-20260814-p0-integration`  
> Last Updated: 2026-08-14

## 1. 目标

在不合并 `main` 的独立集成分支中组合后端完整栈、微信兼容 PUT 路由和前端真实 API adapter，形成可以同时安装、测试、构建和本地联调的 P0 仓库快照。

## 2. 输入分支

- 后端基线：`role-b/feature/TUP-20260814-project-put-compat`，`1bc3cfa`；
- 前端适配：`role-b/feature/TUP-20260814-frontend-api-adapter`，`e8cdd0b`；
- 前端 foundation：`role-a/feature/TUP-20260811-frontend-foundation`，`6dbd568`。

## 3. 范围与影响

- 合并前端 `apps/miniapp/` 与后端 `services/api/`，保留各自 AGENTS 和真实命令；
- 解决 README、开发指南、契约和状态文档冲突时，以已实现并验证的后端契约与最新前端 adapter 为准；
- 运行前后端测试、类型检查、构建和本地 API smoke；
- 不修改数据库 schema、匹配权重、权限规则或产品范围。

## 4. 跨角色记录

- 修改/集成方：角色 B，经用户明确授权完成跨角色集成；
- 评审方：角色 A；
- 前端影响：真实 API 模式由 services 层接入，fixture 保留；
- 后端影响：新增 PUT 兼容路径已在独立任务验证，本分支不改变其语义。

## 5. 验收标准

- 两条输入分支的代码、测试、任务和评审文件完整存在；
- 前端 17 项测试、类型检查、H5/微信构建通过；
- 后端全量测试、编译和依赖检查通过；
- OpenAPI 包含前端 P0 使用的全部 method/path；
- 工作区无密钥、`.env`、构建产物或未解决冲突。

## 6. 验证记录

待集成后填写。

## 7. 剩余风险

- 真实微信 AppID、微信开发者工具、合法域名和 staging 未在当前本机提供；
- 角色 A 的最终 UI/产品验收仍需写入独立评审文件，集成分支不能代替该结论。
