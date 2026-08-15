# TUP-20260815 小程序 P0 界面精修评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Reviewer: 角色 B<br>
> Review Target: `role-a/feature/TUP-20260815-ui-refinement`<br>
> Review State: Pending Role B Review<br>
> Last Updated: 2026-08-15

## 1. 评审范围

- `apps/miniapp` 的全局表单控件、标签选择、步进器、状态面板与名片公开确认弹窗；
- 名片、项目岗位、联系中心、工作台、发现项目卡片和公共项目详情在窄屏和宽屏预览下的布局与触控状态；
- 开放岗位“申请交换联系方式”的创建、接受、拒绝、取消、披露和失败状态；
- 项目邀请收到/发出列表及接受/拒绝动作；
- fixture/API 模式、`API-PROJ-02`、`API-CONTACT-*` 和 `API-TEAM-04` 的契约、安全与存储兼容性。

## 2. 角色 A 验证记录

- `npm test`：5 个测试文件、28 项测试通过；
- `npm run type-check`：通过；
- fixture/API H5 与微信小程序构建：通过；
- 后端 `pytest -q` 全量通过，7 项真实 MySQL 专属用例因未配置测试库跳过；`compileall` 与 `pip check` 通过；
- 本地 `8020` 真实 HTTP smoke：接受前联系方式隐藏，接受后双方获得对方名片；邀请在双方列表可见且接受后创建成员；
- 390px H5 截图：名片、岗位、联系中心、工作台、确认弹窗、发现卡片和公共项目详情无横向溢出；
- 工作台两处操作按钮与内容列右边缘对齐，发现页三张卡片均为可点击按钮；
- 点击第一张发现卡片进入对应详情并展示 2 个开放岗位；
- 点击岗位 CTA 后创建联系方式交换申请；待处理不披露，接受后在“联系”展示并复制对方方式；
- “联系方式 / 项目邀请”两级分段在 390px 和 1440px 下无重叠、截断、横向溢出或控制台错误；
- 取消公开名片后，开关正确恢复关闭状态。

## 3. 角色 B 待核对

- 导入 `dist/build/mp-weixin` 后检查常用设备模拟器中的标签、步进器、switch、联系分段和联系名片设置；
- 检查 recipient 只由服务端从项目 owner 派生，`PENDING/REJECTED/CANCELLED` 不返回联系方式，非参与者不能读取或操作；
- 检查 `GET /me/invitations` 的 inviter/invitee 隔离、分页、过期转换，以及接受邀请事务未产生超额/重复成员；
- 在隔离 MySQL 测试库运行 7 项专属用例，并给出 `Approved` 或 `Changes Requested` 结论。

## 4. 当前结论

> Overall Decision: Pending Role B Review

| Finding ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| UI-A-001 | P0 | 原“联系项目组织者”只创建站内会话，无法交换联系方式。 | Addressed：已由 `CONTACT-001` 私有联系名片和双方同意状态机替代；待角色 B 验证权限、迁移和 MySQL 行为。 |
| UI-A-002 | P1 environment | 当前未在微信开发者工具/真机和真实 MySQL 测试库验证。 | 角色 B 在评审环境补跑并记录；本地 H5、内存/SQLite 和微信构建不能替代这些环境。 |

角色 A 的原 P0 finding 已修复，但角色 B 尚未给出评审结论；在评审文件明确写入 `Approved` 前不得将该任务合入 `main`。
