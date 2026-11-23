# Top 10 机制路径报告

离线基础 GraphBundle：`ANALYSIS_RUN:KG_TOP10_BUNDLE:3928c54d-dd66-4f0a-b346-a798c1f70890`。基础候选 10，OptimusKG 精确映射 8，靶点语义关系覆盖 8，靶点—S1 通路交汇 6；外部 overlay 将覆盖扩至 10/10 身份、10/10 靶点语义和 8/10 路径（528 行）。逐药材料位于 `drugs/`。

后续 external overlay 以相同冻结名单独立补入 PHA-767491、PFI-1 的精确结构身份及有来源支持的靶点断言。overlay 版本达到 10/10 身份、10/10 靶点语义覆盖、8/10 靶点—S1 通路交汇（528 行）。这些是离线覆盖结果，不能写成 OptimusKG 原始底图覆盖，也尚未写入当前数据库。

项目级机制扩展包已将有来源支持的 ChEMBL mechanism 直接作用关系、Reactome 组件参与/通路层级和人工审查疾病上下文证据纳入可导入 GraphBundle：最新 run 为 `ANALYSIS_RUN:KG_GRAPH_BUNDLE:7e70628f-7c76-4a2e-9dd5-56004e9c8c21`。包状态 validated，6,866 节点、38,890 关系及逐边 38,890 EvidenceRecords；其中 9 条 ChEMBL Drug→ChEMBLTarget、14 条 Protein→Gene、205 条 Protein→Reactome Pathway、217 条 Reactome 子通路层级关系、11 个 DiseaseEvidence 及 22 条其关联关系。疾病证据路径保留上下文，不形成药物治疗疾病的直接关系。它是项目级图数据包，还没有注册到主 PostgreSQL 或导入 Neo4j。

目前可自动呈现的解释是可追溯证据链和实验交汇：候选/冻结 WTCS → 精确药物身份 → 来源支持的药物靶点或一般关联 → 靶点与 S1 富集通路交集、Reactome 组件参与映射 → S1/S2 转录响应与方向对照 → ER+ 文献背景。不同证据类别分面展示；路径相交不等同于方向传播、ER+ 特异性或疗效因果关系。没有足够证据形成完整机制路径的候选保留缺口说明。

Top 10 单药页面已用 Cytoscape 渲染当前候选证据子图，支持节点/关系/证据类别筛选、缩放和重置布局；点击边打开来源证据详情，包含方向、数据库、原始记录、文献/实验字段以及未评定的证据等级和矛盾审查状态。图限制 120 条关系并显示截断提示。此图来自只读 API 的离线 artifact，未连接本次尚未注册的项目 GraphBundle。

## 可解释链条

候选药物（LINCS ID，冻结 WTCS 条件）→ 精确 InChIKey 映射（如可得）→ OptimusKG drug-gene 原始断言及来源 → 与 S1 差异/富集基因的交集 → S1 富集通路。每条边均可回查 `evidence_records.csv`。

## 科学解释边界

WTCS 是 LINCS MCF7 表达签名与 S1 gene set 的逆关联分数；药物—基因关系来自公开 KG 或单独标识的外部 claim，路径是静态证据交汇。此图不提供结合实验、作用方向传播、药物在 ER+ 肿瘤的因果效应或治疗有效性。无路径的候选继续保留，不换榜。逐药疾病背景做过定向文献筛查，但不是穷尽式系统综述；疾病背景证据单独展示，不据此自动创建药物—疾病图边。
