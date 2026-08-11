# GitHub Metadata Instructions

本文件适用于 `.github/`，并补充根目录 `AGENTS.md`。

- PR/Issue 模板在使用时必须要求任务 ID、需求依据、验证证据、文档同步和风险；PR 本身是可选评审载体。
- 不新增自动合并、自动发布、生产部署或高权限 workflow，除非有 Accepted ADR 和用户明确授权。
- workflow 权限默认最小化，固定第三方 action 版本；禁止在日志中输出 secrets。
- CI 命令必须来自实际工程清单并在本地验证，工程未初始化时不得添加虚构 job。
- 修改合并门槛时同步 `CONTRIBUTING.md` 和相关开发文档。
