# TUP-20260814 前端真实 API 适配层评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Reviewer: 角色 A<br>
> Review Target: `role-b/feature/TUP-20260814-frontend-api-adapter`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-14

## 1. 评审范围

- API 模式与 fixture 模式的隔离；
- 微信登录 code 的来源、access token 的存储和退出清理；
- `ProfileDraft`/`ProjectDraft` 与后端 DTO 的字段、版本映射和微信兼容 PUT 更新路由；
- 401/403/409/422、网络失败、空项目和服务端 requestId 的展示行为；
- `VITE_API_BASE_URL` 配置和 H5/微信小程序构建兼容性。

## 2. 角色 A 结论

待角色 A 在真实联调或代码评审后填写 `Approved` / `Changes Requested`，不得将本文件的 Proposed 状态视为已通过。

## 3. 验证证据

角色 B 将在任务文件中记录实际执行的前端测试、类型检查和构建命令；真实微信开发者工具和 staging 登录需要角色 A/B 共同验证。

后端兼容契约基线为 `role-b/feature/TUP-20260814-project-put-compat` 的 `1bc3cfa`；评审时必须同时核对该提交的 PUT OpenAPI schema。
