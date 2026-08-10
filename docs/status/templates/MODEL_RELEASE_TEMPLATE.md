# <MODEL-VERSION> 模型发布记录

> Status: Candidate | Shadow | Canary | Active | Retired | Rejected<br>
> Owner: 角色 A / 角色 B<br>
> Reviewer: 角色 A / 角色 B<br>
> Date: YYYY-MM-DD

## 1. 目标

- 优化的业务结果：
- 对照规则版本：`match-v0.x`
- 模型版本：`rank-v1.x`

## 2. 可追溯信息

- 训练代码提交：`<sha>`
- 数据窗口：
- 样本/曝光数量：
- 标签版本：
- 特征 schema 版本：
- 算法与依赖版本：
- 随机种子：
- 模型校验和：
- 产物存储位置：

## 3. 数据质量

- [ ] 曝光分母完整且可去重
- [ ] 未曝光候选未被当作负样本
- [ ] 时间切分无未来数据泄漏
- [ ] 用户/项目重复与位置偏差已分析
- [ ] 注销、同意和保留策略已执行
- [ ] 禁止特征未进入数据集

## 4. 离线结果

| Metric | Rule Baseline | Candidate | Delta | Acceptance |
| --- | ---: | ---: | ---: | --- |
| NDCG@K |  |  |  |  |
| Recall@K |  |  |  |  |
| MRR |  |  |  |  |
| Calibration（适用时） |  |  |  |  |

分组与公平性结果：

## 5. 线上阶段

### Shadow

- 时间与流量：
- 特征一致性：
- 延迟与错误：
- 与规则排序差异：

### Canary / Experiment

- 流量比例：
- 主指标：
- 护栏指标：举报/拉黑率、延迟、空结果、降级率
- 停止条件：

## 6. 安全与回退

- [ ] 模型只能重排规则候选
- [ ] 模型格式和校验和已验证
- [ ] 不加载不可信反序列化产物
- [ ] 特征版本不兼容时回退成功
- [ ] 超时、异常输出和功能开关回退成功
- 回退版本：
- 回退操作：

## 7. Decision

- 结论：Promote / Continue shadow / Reject / Retire
- 产品确认（角色 A）：
- 技术与数据确认（角色 B）：
- 理由与后续任务：
