# TUP-20260811-match-v0-1 角色 A 评审

> Status: Proposed<br>
> Owner: 角色 A<br>
> Requested By: 角色 B<br>
> Review Target: `role-b/feature/TUP-20260811-match-v0-1`<br>
> Review State: Pending<br>
> Last Updated: 2026-08-11

## 1. 评审范围

- `match-v0.1` 六项权重和缺失因素重归一化符合产品预期；
- `confidence < 0.60` 标记信息不足，不把缺失资料解释为能力不足；
- reason code 可由前端映射为安全、可理解的展示文案；
- required skill 未满足或无法验证时不进入正常排序；
- 引擎输出不包含学校层级、性别、微信身份、联系方式或自然语言猜测；
- 当前分支只交付纯规则引擎，不提前固定待确认的列表 API 和物理字段。

## 2. 验证证据

- 匹配规则测试：12 个通过；
- 全仓快速测试：41 个通过，2 个 MySQL 专属测试因未配置临时连接而跳过；
- Python 编译与 `git diff --check`：通过；
- 相同输入结果稳定，reason code 和 exclusion reason 顺序稳定。

## 3. 需要角色 A 确认的后续契约

- required/bonus skill 的产品含义和编辑方式；
- 用户方向偏好、时间段和经历的字段；
- 匹配列表信封、分页及 `recommendationRequestId` 位置；
- 前端展示哪些 factor、missing information 和信息不足提示。

## 4. 评审结论（角色 A 填写）

> Reviewed Commit: `TBD`<br>
> Overall Decision: `TBD (Approved | Changes Requested)`

| ID | Severity | Finding | Required Fix |
| --- | --- | --- | --- |
| A-001 | TBD | TBD | TBD |
