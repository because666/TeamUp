# TUP-20260814 项目更新 PUT 兼容路由

> Status: Ready for Review  
> Owner: 角色 B  
> Reviewer: 角色 A  
> Base Commit: `f053007`  
> Branch: `role-b/feature/TUP-20260814-project-put-compat`  
> Last Updated: 2026-08-14

## 1. 目标

为微信小程序 API 客户端提供可执行的项目更新方法。微信原生 `wx.request` 不声明 PATCH 方法，因此新增与现有 PATCH 完全等价的 `PUT /api/v1/projects/{projectId}`，供前端适配层使用。

## 2. 范围

- API 路由、OpenAPI response/schema 和契约表新增 PUT 别名；
- PUT 复用现有 `ProjectUpdate`、owner 授权、版本冲突、状态校验和事务实现；
- API method/path 契约测试和项目更新行为测试；
- 前端适配任务 `TUP-20260814-frontend-api-adapter` 以本分支 SHA 为联调基线。

## 3. 非目标

- 不删除或改变已有 PATCH 路由；
- 不修改项目表、迁移、版本号语义或权限边界；
- 不把 PUT 用作任意字段 merge，仍要求完整项目 payload 和 `version`；
- 不改变其他 API 的 HTTP method。

## 4. 接口与影响

- 修改方：角色 B；
- 评审方：角色 A；
- 新增接口：`PUT /api/v1/projects/{projectId}`，请求/响应 DTO 与 PATCH 相同；
- 安全影响：沿用当前用户、owner 校验和服务端版本控制；
- 前端影响：微信小程序从 `PATCH` 切换到 `PUT`，H5 也使用同一兼容路径。

## 5. 验收标准

- OpenAPI 同时列出 PATCH 和 PUT，二者返回相同 DTO、错误码和 requestId；
- 非 owner、未知项目、版本冲突和非法状态的 PUT 行为与 PATCH 一致；
- 新增测试覆盖成功更新、401/403/404/409 和 method/path 契约；
- 后端全量测试、编译检查、OpenAPI 契约检查和 diff 检查通过。

## 6. 验证记录

| Command / Check | Result | Notes |
| --- | --- | --- |
| `python -m pytest -q tests/test_api.py -k "project_put_compatibility or openapi_contract"` | Passed | PUT 行为和 OpenAPI method/path 定向测试通过 |
| `python -m pytest -ra` | Passed | 74 passed，7 个 MySQL 集成测试因未配置 `TEAMUP_TEST_MYSQL_URL` 跳过 |
| `python -m compileall -q app tests migrations` | Passed | 应用、测试和迁移模块编译通过 |
| `python -m pip check` | Passed | 无依赖冲突 |
| 实际 TestClient PUT smoke | Passed | 401、403、200、409、404 路径均按预期返回，成功响应版本号递增 |
| OpenAPI schema 检查 | Passed | PATCH 和 PUT 同时存在，均有 typed success response |

## 7. 剩余风险

- 微信开发者工具/真机尚未在当前环境运行；需联调阶段确认 request 合法域名和实际 PUT 请求；
- PATCH 仍保留，未来若确认所有客户端支持 PATCH，可另建兼容清理任务，不在本任务删除。
- 本次未启动 MySQL 容器；路由未修改 store/SQL/迁移实现，现有 7 个 MySQL 专项测试因环境变量未配置而跳过，需 CI 的 MySQL 8.4 job 再验证。
