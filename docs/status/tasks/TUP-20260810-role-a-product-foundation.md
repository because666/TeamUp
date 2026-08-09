# TUP-20260810-role-a-product-foundation：角色 A 产品基础

> Status: Ready for Review<br>
> Owner: 角色 A<br>
> Reviewer: 角色 B（接口、安全与技术可行性）<br>
> Base Commit: `0adcd4f`<br>
> Branch: `role-a/docs/TUP-20260810-role-a-product-foundation`<br>
> Last Updated: 2026-08-10

## 1. 目标

在不等待后端框架决定的前提下，形成可供前端原型、后端契约评审和首条 P0 纵向切片直接使用的用户流程、信息架构与页面状态规范。

## 2. 依据

- PRD：`AUTH-001`、`PROF-001`、`PROF-002`、`PROJ-001`
- API：[API_CONTRACT.md](../../architecture/API_CONTRACT.md)
- 数据：[DATA_MODEL.md](../../architecture/DATA_MODEL.md)
- ADR：[ADR-0002](../../decisions/ADR-0002-mvp-ai-scope.md)
- Review：[角色 A 产品基础技术评审](../reviews/TUP-20260810-role-a-product-foundation-review.md)

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

- [x] 梳理登录、名片、项目/岗位发布的用户流程和异常/退出路径
- [x] 建立信息架构、导航和页面权限矩阵
- [x] 编写页面/状态/字段/校验/跳转规范
- [x] 建立 PRD -> 页面 -> API -> 数据字段映射和契约缺口清单
- [x] 完成文档链接、术语、敏感信息和一致性检查
- [x] 建立角色 B 接口、安全和技术可行性评审文件
- [ ] 角色 A 通过 QQ 通知角色 B，并收回可落盘的评审结论

## 7. 验收标准

- [x] `AUTH-001`、`PROF-001/002`、`PROJ-001` 均能追溯到具体页面和状态
- [x] 登录 -> 名片 -> 项目发布纵向切片的正常、校验失败、网络失败、权限失败和未保存退出路径明确
- [x] 所有页面字段映射到现有契约，或以 `GAP-*` 明确标为待评审，不虚构已确认接口
- [x] loading、empty、error、success、retry 和重复提交状态有统一处理
- [x] 不包含后端初始化、工具链锁定或未经批准的 API/schema 变更
- [x] 相对链接、术语一致性、敏感信息和 `git diff --check` 通过

## 8. 变更记录

| Date | Change | Reason |
| --- | --- | --- |
| 2026-08-10 | 创建任务并标记为可启动 | 工作不依赖后端框架决定，可与角色 B 的基线评审并行 |
| 2026-08-10 | 从已推送的文档基线创建独立分支 | 开始角色 A 产品规范工作，不修改后端所有文件 |
| 2026-08-10 | 三份产品规范和技术评审文件完成 | 角色 A 范围完成，等待角色 B 对契约缺口和安全边界给出结论 |

## 9. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| Markdown 相对链接 | Passed | 38 份 Markdown 的本地相对链接全部存在 |
| GAP 登记一致性 | Passed | 8 个 `GAP-AUTH/PROF/PROJ-*` 引用均有唯一清单项 |
| API ID 引用 | Passed | 新文档引用的 8 个 API ID 均存在于当前契约 |
| Screen / PRD ID 引用 | Passed | 7 个 Screen ID 已登记；10 个 PRD ID 均存在 |
| 敏感信息扫描 | Passed | 常见 GitHub/云密钥、私钥和敏感赋值模式无命中 |
| 旧强制 PR 措辞 | Passed | 精确旧措辞无命中；PR 仍为可选评审载体 |
| `git diff --check` | Passed | 无 whitespace error |
| 前端测试/构建 | Not run | 本任务只修改 Markdown，前端工程和命令尚未初始化 |

## 10. 当前状态与下一步

- 最后完成：`USER_FLOWS.md`、`INFORMATION_ARCHITECTURE.md`、`SCREEN_SPEC.md` 和角色 B 技术评审文件已完成并校验。
- 当前阻塞：角色 A 文档工作无阻塞；`GAP-*` 进入公共契约前仍需角色 B 结论。
- 下一步：角色 A 通过 QQ 发送本分支名和评审文件路径；角色 B 按模板返回评审结论。
- 最后相关提交：`9b75965`
