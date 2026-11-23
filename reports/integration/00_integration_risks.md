# 整合风险登记

| 风险 | 证据/影响 | 控制措施 | 状态 |
|---|---|---|---|
| syh 工作树含用户成果 | 主仓库有大量修改和未跟踪文件，含数据、页面、KG 代码和运行目录 | 所有整合在 staging 快照；不 checkout/reset、不清理源目录；逐文件审查 | 已采取快照隔离 |
| syh `.env` 含本地秘密 | 文件存在，但未检查/打印内容 | staging 不复制 `.env`，使用 `.env.example` 和本地独立配置 | 已规避副本泄露 |
| S2 lineage 混淆 | syh 正式 S2 与交付 A+ run 的候选/签名数和 ID 不同 | 两者作为不同 analysis run；记录输入 hash；不得相互覆盖 | 已隔离注册；API 实际导入 A+ 3,943 条条件；仍保留 syh 原结果 |
| Graph importer 版本误认 | 交付 README 指明正式图谱使用旧 importer；改进 importer 未执行 | 不将候选改进描述为已运行；隔离 Neo4j 验证后决定是否采纳 | 正式交付 importer 经 staging 实际导入并重复验证；候选改进仍未替换正式版 |
| GraphBuild 指标口径不同 | 全图 12,899/48,729 与 DiseaseContext 2-hop 12,171/44,932 口径不同 | 报告中显式标出过滤条件；以 query 复验 | 已在 PostgreSQL/Neo4j/API 三层分别实测并标注 |
| 数据库卷/本地实例冲突 | 主机另有运行容器和 8000/5173 端口服务 | 使用专属 Compose project、端口 25432/27474/27687 与专属 volume；浏览器验收改用 18080/15173；不执行 down -v | 已隔离验证；未触碰已有服务 |
| 文件哈希受 CRLF 影响 | 正式数据 manifest 校验字节级且依赖 `.gitattributes` | 保留 `.gitattributes`；避免自动格式化数据/manifest；复制后抽样 hash | delivery 89 项和 bundle 11 项均零 mismatch；完整外部源数据审计仍待做 |
| GLM 在线能力未证明 | 在线 Provider 可执行，但外部 key 未配置，模型服务需用户账户 | 验证 no-key 行为并保留规则模式；不伪造模型输出 | no-key 503 已验证；真实 GLM/cache 生成待配置 key 后测试 |
| zq 来源不可用 | 当前为空且无 Git 元数据 | 登记为空；如有材料需用户补入后方能纳入 | 当前无内容 |
| 交付数据授权与体积 | OptimusKG/LINCS 等大型或有许可要求的原始数据未必可随代码分发 | 通过复现文档注明获取方式、版本、许可和 hash；不复制 node_modules/数据库秘密 | 文档已有来源/复现入口；仍需面向目标清洁部署核验完整授权与文件可用性 |
