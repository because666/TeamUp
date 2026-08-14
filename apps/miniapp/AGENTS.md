# Miniapp Instructions

本文件适用于 `apps/miniapp/`，并补充仓库根 `AGENTS.md`。

- 技术栈以 `package.json` 和 `package-lock.json` 为准：UniApp、Vue 3、TypeScript、Vite、Vitest。
- 安装：`npm install`。类型检查：`npm run type-check`。测试：`npm test`。
- fixture 开发：`npm run dev:h5` 或 `npm run dev:mp-weixin`；真实 API 模式使用带 `:api` 的开发命令。
- API 模式必须配置包含 `/api/v1` 的 `VITE_API_BASE_URL`；非本地地址使用 HTTPS，微信 code 和平台 access token 只在 `src/services/` 边界处理。
- 生产检查：`npm run build:h5` 和 `npm run build:mp-weixin`，两者不得启用 fixture 模式。
- 页面不得直接拼 API URL、解析 token、模拟服务端授权成功或访问数据库结构；所有请求经过 `src/services/`。
- fixture 必须带 `_fixture: true`、`contractStatus: "PROPOSED_GAP"`、相关 `GAP-*`，并只使用构造数据。
- 新页面必须覆盖与风险相称的 loading、empty、error、retry、401、403、409、重复提交和未保存退出状态。
- 使用 `uni-icons` 提供的熟悉图标，不手绘 SVG；交互控件保持至少 88rpx 触摸高度。
- 新增依赖、环境变量、命令或构建目标时同步本文件和 `docs/development/DEVELOPMENT.md`，并实际运行验证。
