# 7. iniparib EvidencePackage

## 候选与 S2 筛选依据

- LINCS perturbagen：`BRD-K11153516`；主条件：MCF7 / trt_cp / 10 μM / 24 h / distil_cc_q75≥0.2。
- WTCS=-0.455273；项目记号 reversal_score=0.455273；签名数=1；签名 ID：REP.A005_MCF7_24H:P01。
- 历史 B200 置换经验 P=0.0004997501249375312，BH FDR=0.0039334146486079，置换数=2000.0。该检验只覆盖 Exp008 历史 B200 分析集；NA 表示未在该历史文件测试，不能当成不显著。它不是临床疗效概率。
- Exp006 历史稳定性：A rank=58.0，B rank=4.0，稳定性等级=low；可用 24 h Q2 剂量数=4.0，跨剂量负 WTCS 比例=0.75；限制=single signature; QC threshold sensitivity or missing threshold result。
- S1 规模敏感性同条件排名：A_original=243.0; B100=416.0; B150=100.0; B200=16.0; B300=28.0; B_matched125=243.0。全局结果显示 B100/B150/B200/B300 相对原始 A 的 Top10 重合分别为 8/10、7/10、4/10、3/10，故头部名单对 S1 规模敏感。

## 已知靶点和关系语义

精确 InChIKey 图谱映射：exact InChIKey；GraphBuild=`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e`。仅报告当前构建中存在的关系：

- PARP1 (`ENSG00000143799`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `a432a020e64f0128551066b50f61682f0b9f900003e8c51b22b90f1b671e8385`。S1 direction=UP; logFC=0.61397228441878; FDR=0.010940789219611。

## 靶点到疾病异常通路的证据路径

- `PARP1` → regulation of DNA-templated transcription elongation (`GO:0032784`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `3362e2b243d32ec090ee19bdfc554415aef4b921807faa8ffe2b481aaa73374b`；疾病通路关联 ID `5c86225892d7b1ad5d31521c9a8b6c20e17b8716349c9c5edfb5982162390f72`。
- `PARP1` → DNA-templated DNA replication maintenance of fidelity (`GO:0045005`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `7e6d8cf294f8924c795ef00f33523954d4d43230a9e8c38503b51cbd4599543d`；疾病通路关联 ID `3de90415dd5bba97604641ac38088ef7d332b61e6d85f88c8b164d0166c019f3`。
- `PARP1` → negative regulation of chromosome organization (`GO:2001251`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `a18fa941d31369235cabc201eece1f0fe3004efc8d487133c0d182a6ea51fb70`；疾病通路关联 ID `f15cc7c01ad6bef28fafc1bbc135d4074615c0c589333cb28611b8f4742bf18f`。
- `PARP1` → regulation of transcription elongation by RNA polymerase II (`GO:0034243`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `a968511ebfa5316984612ac71b1fda7d3181a63c2637f74d0ff38a51b9e31e3c`；疾病通路关联 ID `ebf2fce7dbe228fbf4b09f96dd5efe62b6db2ad85ad24f0d7e32dcf2f648bd9b`。
- `PARP1` → negative regulation of transcription elongation by RNA polymerase II (`GO:0034244`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `eeb0b222b0e49797d43e2b482c9ece9810722faaab90470f0eb56d2b24d4f782`；疾病通路关联 ID `1db3696778df3c8a2f144d0778809e322132bfb8502c4c0fbec9c650eee25694`。
- `PARP1` → regulation of double-strand break repair via homologous recombination (`GO:0010569`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `ebd331fdc3f7da2a31eb3b95e8aab10bf3039ef164693cc13dd86e26de59a818`；疾病通路关联 ID `6774abd478d3265b5b5a7a2a348ba2c3eb855762cca01268342dc5e17f01c7ec`。
- `PARP1` → positive regulation of double-strand break repair via homologous recombination (`GO:1905168`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `5ea8716d460301ec0863b65e98998231385c37109efeae448b2ac71cb09c4a8f`；疾病通路关联 ID `897fe7c5e79be4d9f694bc77af2637537fc054ba6ede715d2d3b41d72df12d80`。
- `PARP1` → Homology Directed Repair (`REACT:R-HSA-5693538`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `1b567bce76cd45d6001045b13bfcd0d740c1a16fd90ca192fe0f5bce95bc43b5`；疾病通路关联 ID `d82b5f7a5849e39d5c75b3253d903c7483bc0a2fa13153b6de02b582cbe8bc80`。
- `PARP1` → DNA-templated transcription elongation (`GO:0006354`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `57c9b46e8cc8282aaa983d03a77eb091a20fb3768303b338f229ee12727a68a2`；疾病通路关联 ID `bb3df6d079bd04f817757db6b22e58b3ece5708b3ae051b78cf54c1d9b0ce525`。
- `PARP1` → double-strand break repair via homologous recombination (`GO:0000724`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `96cb561ebc14cadb8691f45c82e79984349da51977ce8ad12fd3fc748272e98d`；疾病通路关联 ID `22d7970778aa22b9d8e04ef34df8075c3f4b5eb9ca6c5a6f82a8a552a9611b48`。
- `PARP1` → cellular response to UV (`GO:0034644`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `ce0c5cc87e02520a38f8e38ad7b4bc13e1e1f8ad5d6baa259ef4d50c21f9d017`；疾病通路关联 ID `ff02abc4241593fee5bbcede92d28935c8432616b1ca24525e4f682dc0fbb294`。
- `PARP1` → base-excision repair (`GO:0006284`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `adb423b6b115d85c20453c17344b67b86c5fcc210b17ed03c60db6fc321900e1`；疾病通路关联 ID `a317ee6f918d215b624a7277540170e155fe958aa002970d2b872242c1ae7328`。
- `PARP1` → positive regulation of double-strand break repair (`GO:2000781`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `8f58bc0b0c0d2fe43bb7a59c6a59288ea9f64042de21f0200808f6b3b2308fb7`；疾病通路关联 ID `415ecc96a53048d1bff3111dd1407c7961983739e440f6900630a69d26dff3fe`。
- `PARP1` → regulation of DNA metabolic process (`GO:0051052`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `f5621fe5d03da6b3607689ad50136d01eed5d186ee7476c7c8af43f7a371ddf1`；疾病通路关联 ID `80a19562de3f615c4b3afdd63e62c36b0e8b26d00a31f0ff4bcede74154a0245`。
- `PARP1` → protein localization to chromosome (`GO:0034502`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `b79b19c8efe100b066f49a54b84adf7383dba0758d47f86ae8f14d49d4fcbd8d`；疾病通路关联 ID `acb28da4a278440c0b811354def5650e21394494f44982094bac6ec214282a5a`。
- `PARP1` → DNA Repair (`REACT:R-HSA-73894`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `1e391a95b34a19c57b73d25f8f9bed2a54bd21fda7b3d82b6efaa9cac8fa6ae3`；疾病通路关联 ID `4db154d94c227e18b5b461889d39ca211b0419495a411153d2e43950a7489f50`。
- `PARP1` → DNA recombination (`GO:0006310`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `2690c503b5d0f31f638eb30004c0828f4f58bcf441020ab740b49a39e7a46bd9`；疾病通路关联 ID `2aeb3db619bb95ddf4b5f8b5a42e94115c4b6be3b01d82ca4548477c9535b97f`。
- `PARP1` → positive regulation of DNA-templated transcription, elongation (`GO:0032786`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `1316880926af317e999c5ae71f87ba745247f141cbc90733eaac42a57b8cdca8`；疾病通路关联 ID `4ff9caf4845e7764be566660fe3180e0da700d1ff0ab7bb1b6d383bd6c9c7325`。
- `PARP1` → recombinational repair (`GO:0000725`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `7b17da3375cd3365c2631061b06a1c57ffe03e751d213362d36c1b5040d61861`；疾病通路关联 ID `7b958db2b1bcadebf92414a400b21a2fd8183085cf5003b6fbe70ac703f21221`。
- `PARP1` → Resolution of AP sites via the multiple-nucleotide patch replacement pathway (`REACT:R-HSA-110373`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `577737fb5eaa62971be96aff97d710e26eeadd585ea9d22569deebdd5cb67814`；疾病通路关联 ID `be4bf917bffd5d9704ec4a72359818c3f2ba675a134364b1d17bb4778a179e9f`。
- `PARP1` → positive regulation of DNA metabolic process (`GO:0051054`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `27f857d04710954fcda67c3e3a73a73f29092ae95f8949a3efa83cdef4bb2835`；疾病通路关联 ID `d8b00928fa9c8fa2dcdf022bba8062b63549ddafe2ee88c7a5f5d751bb4434d6`。
- `PARP1` → positive regulation of DNA recombination (`GO:0045911`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `62e9497e4b2e26adef900cd63ab534204df6358b2260d2366373e335b44b7a84`；疾病通路关联 ID `ee5e173800e78854cad9a57ea1bef27de18229ab44f143ed11f57bb271a01a86`。
- `PARP1` → negative regulation of DNA-templated transcription, elongation (`GO:0032785`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `7e9282e4abaa93d5e81b1e8c6083e94f01ed55e08423d2170f9a84899fbce2ba`；疾病通路关联 ID `a229780e30ad6892ee427c1e600d1b275e86bd841a4126a65142b89332e7af9e`。
- `PARP1` → DNA-templated DNA replication (`GO:0006261`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `ae8996ec71872b565a79fa8572889b6d180162c29f5cb06eafaa870add63890b`；疾病通路关联 ID `4cc03e787c5aacdedf31a4fa35666b9116dd9dd0b53f57214727dc4a3209ad4e`。
- `PARP1` → SUMOylation (`REACT:R-HSA-2990846`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `69151288194b7af7d7798dc6fb49efdb93fff254683af1896c618f4f2b2db6f4`；疾病通路关联 ID `e14ca93b77ffb37756ae7341ca632a510a5be19c7f07ea80ffcae51b763b725f`。
- `PARP1` → telomere maintenance (`GO:0000723`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `65160a1074d3fefcbf75010ed4d87af9ecf00a2ac4c9217392e6ad44cd6166cb`；疾病通路关联 ID `60383503cde08e058361dbd4a2e0609b8bf00e0576b9e458d23f3dcc57045c2a`。
- `PARP1` → replication fork processing (`GO:0031297`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `b9494b723910ad9a89a8234dff11a2dc046f18fbf446c82406c61c6f54d485a0`；疾病通路关联 ID `eab77271c6d623a968050340d257e0dc32435aba12546dc44ba240c403d6bbfb`。
- `PARP1` → regulation of DNA repair (`GO:0006282`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `b4bc518b4945b540e028191bc880d58cccf84c66e905395929a10936b630a9d5`；疾病通路关联 ID `731b429c5c2de9c3571e9ffaf325edd91e072e148027b00c7cc0808397bf0064`。
- `PARP1` → positive regulation of DNA repair (`GO:0045739`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `d69e9d57c454e5813bc215ec42ca5641210508e7efdab2d63bb445ea08b9f3cf`；疾病通路关联 ID `ccdabf34c69f5c0e531116b37661e90db5e5d2ab34f798f85aafe3ffd1260df3`。
- `PARP1` → DNA replication (`GO:0006260`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `ea23d93e9b4c40acbd44a4fdc5aa79809b0e1f461b64392dd38531b60a32e9fc`；疾病通路关联 ID `c1cbf243564b5f3629f5a676240923f621a38bdadac87e9bcfedd82a99273eee`。
- `PARP1` → regulation of double-strand break repair (`GO:2000779`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `8a1caa3c84857cad11316690fc9d572cc5eb597bb8b91db700ff80c24ca34388`；疾病通路关联 ID `b07d14da7ff008020e8e9e859bb3a7b23605e6ae101a31e2e7663c1320ade612`。
- `PARP1` → double-strand break repair (`GO:0006302`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `70b04c83b7dfcdc6aee36eae82f6cf51fed1a8d12902990b610fa9bab816353b`；疾病通路关联 ID `e703aaa96ac3f7721e319d47a2b55a2eb32da1e251e4f6752e62e449c1b88f03`。
- `PARP1` → Base Excision Repair (`REACT:R-HSA-73884`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `f64d6aa746f01b8453d665d73e2e660e7bf50417169b848df222bfea8b450d5c`；疾病通路关联 ID `911e73dbcbf9517e61fad74c80d91527063b12a83008977018872406310665f6`。
- `PARP1` → SUMO E3 ligases SUMOylate target proteins (`REACT:R-HSA-3108232`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `46544ccb2e4726b778e36c951a68bab0cc9d8a994196cf54cb6b05e438921f4c`；疾病通路关联 ID `21ece173843704f662c2dde69996ebaf6c1b106d485852a804e9801eed6d8feb`。
- `PARP1` → Resolution of Abasic Sites (AP sites) (`REACT:R-HSA-73933`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `4fd330cd079e4c9128814881a1783ae4156919f0e7ba677282652793e7024afe`；疾病通路关联 ID `58c024fe81abdedc212a9d7fde7e3520698f6a66c626112ef360f0476b6b4d33`。
- `PARP1` → transcription elongation by RNA polymerase II (`GO:0006368`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `a39446de0362666d67d54071cf6077a6132b7ab08892ee74474c1971ea29fae2`；疾病通路关联 ID `7091135150da03b0442119f9eb5f04572078c298af7b1204eee4e04b9e817624`。
- `PARP1` → regulation of cellular response to stress (`GO:0080135`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `6708b0f26fda91b072953ef17bc01dc3fb609e308ff41961ebdf514648dd3c4b`；疾病通路关联 ID `25f9d170ab2c558f36f69541b58873dbacd2ec6ffd7c18ba09781e280b7a5141`。
- `PARP1` → telomere organization (`GO:0032200`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `7f4c6cfc948ac3857225ce707f1cde391767b54106f0524a6cc7d1b53faab07d`；疾病通路关联 ID `47f7306648b64e644b229bc50ecd033ffb35d6db48ab9370cda1885ec1981779`。
- `PARP1` → regulation of chromosome organization (`GO:0033044`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `37c0d9a780ed2f410750bac27bd711c30655b2df2454507877a185b1037995b7`；疾病通路关联 ID `3084b0ae2344662260fc2e35cfc78a12067c5cad3cae051314bf792647855180`。
- `PARP1` → DNA Double-Strand Break Repair (`REACT:R-HSA-5693532`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `068623b2e70a94bc7f32470db7562e0d492ffd6b09631ab7b6071701b3fe0d44`；疾病通路关联 ID `0259e3d282b8ec51ab5b1492f822f5d9b7748243eac57cab7e63a595e6c55bc4`。

当前 S1 富集摘要：肿瘤上调侧突出 DNA replication、E2F/G2M 与 estrogen-response Hallmark；肿瘤下调侧突出氧化代谢、呼吸链/oxidative phosphorylation、脂肪酸代谢等。富集与路径重叠仅为注释关联，不是通路因果证明。

## 独立验证、机制假设与冲突证据

- Exp010 独立队列同条件排名：155.0；外部 S1 条件级排序与主排序总体 Spearman=0.544，Top10 重合仅 1/10。
- PRISM ER+ 平均敏感性：0.2234544371641，细胞系数=9.0；PRISM 相关性弱且没有显示 ER+ 选择性，不能作为 S2 药效确认。
- 候选机制摘要：本图谱仅有 PARP1 一般 TARGET 关联，未记录抑制语义；外部研究对其完整细胞 PARP 抑制作用提出反证，故不将其解释为已验证 PARP 抑制剂。
- 文献链接：[https://pubmed.ncbi.nlm.nih.gov/22291137/](https://pubmed.ncbi.nlm.nih.gov/22291137/)。
- 本项目用确定性证据模板整理解释；未调用 LLM 生成本候选机制正文，因此不把模板内容标为 AI 输出。

## 局限

该药主条件仅由 1 条 LINCS signature 支持。WTCS 是表达逆关联，不等同药效。靶点关系与机制文献可能来自一般药理，不代表在 ER 阳性乳腺癌中直接成立。当前图谱没有可审计 PPI 边；不推断一层 PPI 扩展。后续需要多签名/剂量的重复、ER+ 模型剂量反应、正常细胞对照和机制实验。

## 可追溯文件

- S2 原始评分：`results/final_signature_scores.csv`（signature ID 可检索）；候选证据：`results/final_top10_evidence_matrix.csv`。
- 图谱关系路径：`mechanism/top10_mechanism_paths.csv`；原始图谱查询结果：`mechanism/final_neo4j_direct_targets.csv`、`mechanism/final_neo4j_s1_pathway_links.csv`。
- 逐条引用登记：`mechanism/top10_evidence_citations.csv`。
