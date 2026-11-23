# 建设前后覆盖对比

| 指标 | 旧 Top 10 只读查询（GraphBuild a6aabb2147cb5f5e） | 本次离线 Top 10 GraphBundle（OptimusKG 3.2 + 正式交付快照） |
|---|---:|---:|
| Top 10 候选 | 10 | 10 |
| 精确 InChIKey 映射 | 5/10 | 8/10 原始 OptimusKG；10/10 加独立外部 overlay |
| 靶点语义药物覆盖 | 历史报告记录直接靶点 5/10；未按统一白名单复算 | 8/10 原始 OptimusKG；10/10 加来源明确的外部 overlay |
| 靶点→S1 通路路径覆盖 | 5/10 | 6/10 原始构建；8/10 加 external overlay（总 528 路径行） |
| S2 条件 | 旧查询绑定原始 Top10 条件报告 | 51 个 A+ 选择条件完整保留 |
| 图规模 | 不适用：查询表而非独立 Top10 bundle | 基础 external overlay：6,643 节点 / 38,394 关系；项目级 ChEMBL/Reactome 扩展包：6,855 节点 / 38,868 关系 |
| 可追溯机制档案 | 旧 GraphBuild 有 10 条候选记录但证据语义/路径覆盖有限 | 10/10 有逐药档案；目标语义覆盖 10/10（8 个 OptimusKG + 2 个独立 overlay）；S1 通路交汇 8/10（外部 overlay） |
| 疾病背景与反证筛查 | 未形成一致的逐药 ER+ 证据表 | 定向筛查 10/10，保留亚型/模型/方向/限制；非系统综述，且不自动创建药物—疾病关系 |
| 机制证据分级 | 无统一逐药等级 | 按方案 A/B/C/U 对 10/10 人工定向审阅（A 3、B 6、C 1、U 0），保留理由/来源/限制；不代表疗效概率 |
| Exp006–Exp011 复核入口 | 已有实验结果分散在实验目录 | 新建冻结候选逐药汇总文件；Exp009、Exp010、Exp011 当前各覆盖 5/10，缺行是未覆盖/未匹配 |

该比较仅比较离线覆盖产物，不能说明 Neo4j 已更新；任何新图包均未写入主数据库。项目级扩展包增加 ChEMBL target entity、protein/gene 和 Reactome pathway/hierarchy 关系，并保留逐边证据。旧 GraphBuild、Top 10 bundle、外部 overlay 的数据源范围不同，覆盖变化不能归因于单一因素。原始 OptimusKG 覆盖与外部 overlay 覆盖必须分开报告。
