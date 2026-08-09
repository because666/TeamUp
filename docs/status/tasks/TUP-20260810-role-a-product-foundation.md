# TUP-20260810-role-a-product-foundation：角色 A 产品基础

> Status: Ready to Start<br>
> Owner: 角色 A<br>
> Reviewer: 角色 B（接口、安全与技术可行性）<br>
> Base Commit: `f968335`<br>
> Branch: `role-a/docs/TUP-20260810-role-a-product-foundation`<br>
> Last Updated: 2026-08-10

## 1. 目标

在不等待后端框架决定的前提下，形成可供前端原型、后端契约评审和首条 P0 纵向切片直接使用的用户流程、信息架构与页面状态规范。

## 2. 依据

- PRD：`AUTH-001`、`PROF-001`、`PROF-002`、`PROJ-001`
- API：[API_CONTRACT.md](../../architecture/API_CONTRACT.md)
- 数据：[DATA_MODEL.md](../../architecture/DATA_MODEL.md)
- ADR：[ADR-0002](../../decisions/ADR-0002-mvp-ai-scope.md)

## 3. 范围与交付物

- 新建 `docs/product/USER_FLOWS.md`：角色、入口、正常/失败/退出路径和跨页面状态；
- 新建 `docs/product/INFORMATION_ARCHITECTURE.md`：小程序一级/二级导航、页面归属和权限可见性；
- 新建 `docs/product/SCREEN_SPEC.md`：页面字段、组件、loading/empty/error/success、校验和跳转；
- 定义首条 P0 纵向切片：微信登录 -> 建立/编辑能力名片 -> 创建并发布含开放岗位的项目；
- 为每个页面建立 PRD 字段与现有 API/数据字段映射；契约缺口只登记提案，不自行定稿；
- 提供与契约一致、明确标注为 mock 的前端状态样例，不创建虚假后端成功逻辑。

## 4. 非目标

- 不初始化或修改后端工程；
- 不替角色 B 选择 FastAPI 或 Spring Boot；
- 不在未评审时修改公共 API、数据库 schema、认证授权、隐私规则或推荐权重；
- 不锁定 UniApp、Node、包管理器、测试框架或组件库版本；
- 不实现推荐模型、真实微信登录、部署、CI 或生产配置。

## 5. 依赖与假设

- UniApp 方向已确认，但工程版本和命令仍为 TBD；本任务只产出产品/交互规范与契约 mock 说明。
- 现有 API 和数据文档是 `Proposed` 基线；发现缺口时使用稳定 `GAP-*` ID 登记，并交角色 B 评审。
- 角色 B 对接口、安全和数据字段拥有技术评审权；角色 A 对用户流程和产品行为负责。

## 6. 计划

- [ ] 梳理登录、名片、项目/岗位发布的用户流程和异常/退出路径
- [ ] 建立信息架构、导航和页面权限矩阵
- [ ] 编写页面/状态/字段/校验/跳转规范
- [ ] 建立 PRD -> 页面 -> API -> 数据字段映射和契约缺口清单
- [ ] 完成文档链接、术语、敏感信息和一致性检查
- [ ] 请求角色 B 评审接口、安全和技术可行性

## 7. 验收标准

- [ ] `AUTH-001`、`PROF-001/002`、`PROJ-001` 均能追溯到具体页面和状态
- [ ] 登录 -> 名片 -> 项目发布纵向切片的正常、校验失败、网络失败、权限失败和未保存退出路径明确
- [ ] 所有页面字段映射到现有契约，或以 `GAP-*` 明确标为待评审，不虚构已确认接口
- [ ] loading、empty、error、success、retry 和重复提交状态有统一处理
- [ ] 不包含后端初始化、工具链锁定或未经批准的 API/schema 变更
- [ ] 相对链接、术语一致性、敏感信息和 `git diff --check` 通过

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-10 | 创建任务并标记为可启动 | 工作不依赖后端框架决定，可与角色 B 的基线评审并行 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| 文档与 Git 检查 | Not run | 实施完成后填写实际命令和证据 |

## 10. 当前状态与下一步

- 最后完成：任务边界、交付物、非目标和验收标准已登记。
- 当前阻塞：无；接口和安全结论需在角色 B 评审后才能从提案转为确认。
- 下一步：从当前文档基线创建任务分支，先编写 `USER_FLOWS.md`，再完成信息架构和页面规范。
- 最后相关提交：`uncommitted`
