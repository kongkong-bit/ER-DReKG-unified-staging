# 2. mocetinostat EvidencePackage

## 候选与 S2 筛选依据

- LINCS perturbagen：`BRD-K16485616`；主条件：MCF7 / trt_cp / 10 μM / 24 h / distil_cc_q75≥0.2。
- WTCS=-0.505900；项目记号 reversal_score=0.505900；签名数=1；签名 ID：LJP008_MCF7_24H:I07。
- 历史 B200 置换经验 P=0.0004997501249375312，BH FDR=0.0039334146486079，置换数=2000.0。该检验只覆盖 Exp008 历史 B200 分析集；NA 表示未在该历史文件测试，不能当成不显著。它不是临床疗效概率。
- Exp006 历史稳定性：A rank=7.0，B rank=2.0，稳定性等级=low；可用 24 h Q2 剂量数=6.0，跨剂量负 WTCS 比例=0.6666666666666666；限制=single signature。
- S1 规模敏感性同条件排名：A_original=42.0; B100=79.0; B150=10.0; B200=2.0; B300=2.0; B_matched125=42.0。全局结果显示 B100/B150/B200/B300 相对原始 A 的 Top10 重合分别为 8/10、7/10、4/10、3/10，故头部名单对 S1 规模敏感。

## 已知靶点和关系语义

精确 InChIKey 图谱映射：exact InChIKey；GraphBuild=`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e`。仅报告当前构建中存在的关系：

- HDAC2 (`ENSG00000196591`): 关系语义 `TARGET, INHIBITOR`，来源 `DRUG_BANK; OPEN_TARGETS`，Evidence ID `99bca6f28a0cc98506c69cb3c4ca8fd3913bba5108c408fa429deb210e0aa19c`。S1 direction=—; logFC=—; FDR=—。
- HDAC11 (`ENSG00000163517`): 关系语义 `INHIBITOR`，来源 `OPEN_TARGETS`，Evidence ID `9d1ad02de8ffe6b1351484925bcd52c2c18e4fcfcd4036023a06f40361d450a7`。S1 direction=—; logFC=—; FDR=—。
- HDAC8 (`ENSG00000147099`): 关系语义 `INHIBITOR`，来源 `OPEN_TARGETS`，Evidence ID `3b5ab53e8a33331ae2064f31b55b490d879e8d23e15df515fa253a63222ca9ec`。S1 direction=—; logFC=—; FDR=—。
- HDAC3 (`ENSG00000171720`): 关系语义 `TARGET, INHIBITOR`，来源 `DRUG_BANK; OPEN_TARGETS`，Evidence ID `5287e6deb3b2093e54b83c44397c5cbee5ed5ed2eb2c642cccb987decb747fe4`。S1 direction=—; logFC=—; FDR=—。
- HDAC1 (`ENSG00000116478`): 关系语义 `TARGET, INHIBITOR`，来源 `DRUG_BANK; OPEN_TARGETS`，Evidence ID `27730fe8fcc8d1fb1d5f67982ee4ce2ad4b2427cf8a2d78e34dd0187495f4c9d`。S1 direction=UP; logFC=1.09654237112642; FDR=0.000132622994771007。

## 靶点到疾病异常通路的证据路径

- `HDAC1` → viral transcription (`GO:0019083`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `3cdcc2ba72eb2440dcfd3c779e72f991a5e35106e292b5008a453669665d16f5`；疾病通路关联 ID `a1a652c447230b6b2e65ab8e22f59d120aeabd8c37b33e38d63006e44af18465`。
- `HDAC1` → heterochromatin formation (`GO:0031507`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `a4b1fdad70f91f3d37fe00813365af870ecd2d5c431be798577f793ae32541ee`；疾病通路关联 ID `83101b07b846fa1381e75815475bceb346d7cd85f159d290d9d8e738351f8d13`。
- `HDAC1` → viral gene expression (`GO:0019080`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `9d795c385355fb7c12b9b7bc9fe810c911e948eaae60b02775d9456aeebbd3b2`；疾病通路关联 ID `d41cbac42612096aab84113da81feeb18676c93542a74d5d1f81958eb763cf8f`。
- `HDAC1` → RNA Polymerase I Promoter Clearance (`REACT:R-HSA-73854`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `aba179d378530c657e856fdaefc990236feb994fd539e95e17fe724210d0f8e3`；疾病通路关联 ID `82a32882b61cf50998e506c0a13122a7acd4a8994b1794d9fbe51d1377e9f516`。
- `HDAC1` → Death Receptor Signaling (`REACT:R-HSA-73887`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `c44f4a220d411f2c5e38c00919ad97d532c7d4471344e0c46d045d4527a25b42`；疾病通路关联 ID `f4cbb3ad804c245cc1a4ec4f0958d67e3330377a3cc164471f7961dd7383671c`。
- `HDAC1` → Regulation of endogenous retroelements by Piwi-interacting RNAs (piRNAs) (`REACT:R-HSA-9845323`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `0bdd0716bb2e321b8c4bf003a45c45ae1eb771f2185b11cff3898b73068d8c2b`；疾病通路关联 ID `5bf63a80a02d79821572fcf1a5ef7dbcef580e5151829ce4daa2a0f675bb5c82`。
- `HDAC1` → Factors involved in megakaryocyte development and platelet production (`REACT:R-HSA-983231`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `b689ebb1a539e1a4902409d21a6733217eaa4ca3322ec7719ece61e9746bfd3c`；疾病通路关联 ID `46c437ccebc25565c32d136b394db64ea0faaa10273c669a472c643545671c51`。
- `HDAC1` → Regulation of TP53 Activity (`REACT:R-HSA-5633007`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `7f8f425037753d28a156fe444029647dff312214aafebcec481a2fe03992fe12`；疾病通路关联 ID `0c2079b1d2e8c19f31a65b793d88cd36f4b2b4b28c81e3c91feed48db75dc478`。
- `HDAC1` → SUMO E3 ligases SUMOylate target proteins (`REACT:R-HSA-3108232`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `56359dff3e2aab3e1324b8fc812cfa169c2ac2f3cd859f0dfc9b89b5e8a69065`；疾病通路关联 ID `21ece173843704f662c2dde69996ebaf6c1b106d485852a804e9801eed6d8feb`。
- `HDAC1` → regulation of stem cell population maintenance (`GO:2000036`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `82d51e9f174b2c046a8db78603ac4c918e9b81725aae6646809606ce02629a52`；疾病通路关联 ID `61d8afeb2003f1ab9f99db31b567a1984a69370b3d81f92efa90943da612067c`。
- `HDAC1` → Formation of the beta-catenin:TCF transactivating complex (`REACT:R-HSA-201722`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `7880d98320dcf8df7405911509f129cec5df3c71bfab3f1bf76dc24cd791f78b`；疾病通路关联 ID `92a56bc149d5c9100255c0745deac4c2a47ebc9cce5a1a6a78aab81443b4648c`。
- `HDAC1` → NoRC negatively regulates rRNA expression (`REACT:R-HSA-427413`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `4e9684d4a50234d40d2190cb70cc1d322ba517fb9071eb697571214caac24976`；疾病通路关联 ID `8f3968b2708b02bd7ee335bcb9467ed53823b9aeebd9fe81837585e29312573c`。
- `HDAC1` → Negative epigenetic regulation of rRNA expression (`REACT:R-HSA-5250941`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `aa2c3b0182bd80a533c90fa7a93a2a0ce6368f84cbbdedc0c98f0784af43c2cc`；疾病通路关联 ID `48810300d7f51f3d33f54b4d2b09ecf9a0fbb4a812462b3e442870a9f225b20d`。
- `HDAC1` → RUNX1 regulates genes involved in megakaryocyte differentiation and platelet function (`REACT:R-HSA-8936459`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `1d87026b43d45dfe4fd2c6e80c3d45bf846e4453a4b37f14c205f22fa2c21cb0`；疾病通路关联 ID `1a7b36cafb80c7c9c0fbfa9e1625bc7081bbb16ed9ba5f602e03858980a4509c`。
- `HDAC1` → Epigenetic regulation of gene expression (`REACT:R-HSA-212165`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `5535c4b8fcee531693f7e591a026b698edfc012ee1db589e306afb1c0f21a7f0`；疾病通路关联 ID `2db2558b1a9af6177bf90a28825999bb7af8e44c4015fbf36ed5958e24de7226`。
- `HDAC1` → Regulation of TP53 Activity through Acetylation (`REACT:R-HSA-6804758`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `d731c0feb77d86506a330f8fcb77933cb79fadf798a374fc0cc1d939dde44c6e`；疾病通路关联 ID `34dabdad008e9ddec9ed5c8c2ac717f18ab0d589e8e73353cc0a3f682a4faf80`。
- `HDAC1` → Chromatin modifying enzymes (`REACT:R-HSA-3247509`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `25aaced62a3322fd57808cf1fc1697dc2750605864ba43b0cd3afd52dc3eddd6`；疾病通路关联 ID `d11328e7632d8e5f43bfe40cf65afef3b265c1e9b784a0ac4698bf38b7be776d`。
- `HDAC1` → viral process (`GO:0016032`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `ff63467c47ebc445b91126ed6570df55f6fc1b0b18b1ea33c350f20e2249c049`；疾病通路关联 ID `5276adb6c99a8a3c62c203bc44c701fff56818b21cb46d60eddfb66f0f855f96`。
- `HDAC1` → Regulation of endogenous retroelements by KRAB-ZFP proteins (`REACT:R-HSA-9843940`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `3d404beeed01db6d0ccd38d2e3f1880ac0671a05b5ab7c544499c768f786d624`；疾病通路关联 ID `76d68a65bfcb583cf8becba923159a443c2edbc50b318b7547455e604080e03c`。
- `HDAC1` → Regulation of endogenous retroelements (`REACT:R-HSA-9842860`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `89644a9666ea8f3342a9217b51e5f7d2c44bcd49698a8a3ec179ad5103a15360`；疾病通路关联 ID `4b4d9d7d88065a5b379f713823a5d2295e3b7f0bf930eb6db5de8a3c7a856374`。
- `HDAC1` → Chromatin organization (`REACT:R-HSA-4839726`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `879b8d0257d702c83cd00151f28deb71de981eefc732388b8f24e666d37eeea9`；疾病通路关联 ID `8ee3db2a32abd6eec911ac2256fc19a69266c3c65ebf752bbe2a79c60d2628a0`。
- `HDAC1` → SUMOylation of chromatin organization proteins (`REACT:R-HSA-4551638`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `c769ad2b9a1932fa175378f84454799807e4fd00f1ad264e8e058a2e4a4a3412`；疾病通路关联 ID `9bc979c9b46259609c98027cd259252e440466b64a506b69cfa731cc37c4eed6`。
- `HDAC1` → Positive epigenetic regulation of rRNA expression (`REACT:R-HSA-5250913`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `a0232e92af6f0bb653d3b03f50011c4d61f1e2ac9a3182df690a8d3c17758ea2`；疾病通路关联 ID `97fd41f7affe4b168bdb6ba31314de35f79adbc2efdd15b568f55ffe6a0df26e`。
- `HDAC1` → Cell Cycle, Mitotic (`REACT:R-HSA-69278`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `98a9f4d0c57655373cabc41a80dcdb6dc5a4bf5f9318d335d43ff2de9a7190c1`；疾病通路关联 ID `b9e3d9d250aabd88ba397199e5a68d34a56ee0f6410c038bf9c6f6488643b117`。
- `HDAC1` → ESR-mediated signaling (`REACT:R-HSA-8939211`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `99c6cfe1fe7e0955a921160e512b78dd1636c95dd0cf1799c552c9369875d39e`；疾病通路关联 ID `10c8ccd56aa0d59c20cadb06eb3cdc433f88c6e9c17aff3a960fbb4e31313834`。
- `HDAC1` → HDACs deacetylate histones (`REACT:R-HSA-3214815`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `68896a8016476830e885ade511a1f90f76fd8ffd76e10eda5066a51eb7714928`；疾病通路关联 ID `415ba5d0f9dc9e9a0e9ec6eac3d58eda73efec1f5b652e2ce984ac577b7a9717`。
- `HDAC1` → SARS-CoV Infections (`REACT:R-HSA-9679506`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `bbc11479ea4b27e7ead9d5821fe39930009df135d3dadee56948374a5bdd5cfe`；疾病通路关联 ID `50f8230723c5b5d5961e1373f14d239f346a3a403c8d4de1d60d7378705699a1`。
- `HDAC1` → p75 NTR receptor-mediated signalling (`REACT:R-HSA-193704`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `85c61bd5f48fc57db51bb303086e796ecd1ae1e5a3a122a0306afaf88c822be3`；疾病通路关联 ID `563cfb6c92dd7f2a228c36bfb76c92e768db6a34f4af113ceb4d59a19a448ace`。
- `HDAC1` → RNA Polymerase I Transcription Initiation (`REACT:R-HSA-73762`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `119e8262b4b28e78d7bb1e12b91d5ef14f4366b9cb933cb25654a4ab2a64dbcc`；疾病通路关联 ID `d08569726afb8dc16b4da70688673094b65830548b5465e11414e5cc1fad1930`。
- `HDAC1` → Transcriptional Regulation by TP53 (`REACT:R-HSA-3700989`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `a15074e324f7d0b30bdf0c6223ca8faf472b46eafb4479f5a4033c8da1cce035`；疾病通路关联 ID `12d4d2350fca71e887692e0816c6a5c2146bc44cf61f5dac72ab4463f4e81dee`。
- `HDAC1` → SUMOylation (`REACT:R-HSA-2990846`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `29b767f2c15d4947ec890e31cb33c06d601515b103b5e55e8a3c82b7b2a5a84e`；疾病通路关联 ID `e14ca93b77ffb37756ae7341ca632a510a5be19c7f07ea80ffcae51b763b725f`。
- `HDAC1` → positive regulation of stem cell population maintenance (`GO:1902459`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `eb2b4edfc13e703628a471ddb38f88bd66a1aa7a63889483d2d318f56752d1a1`；疾病通路关联 ID `ac03e463677928d11ef541b74c706957196b53273edddd2165a2716b2d01be22`。
- `HDAC1` → ERCC6 (CSB) and EHMT2 (G9a) positively regulate rRNA expression (`REACT:R-HSA-427389`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `f53d7223e9366b528d76ba10881cd8d5fe8f7a018acfc9a5c06c87f08ba51068`；疾病通路关联 ID `06587910234c22ad136540c9bbcf169d6219812f2b552be6470164e609fdc713`。
- `HDAC1` → Estrogen-dependent gene expression (`REACT:R-HSA-9018519`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `1544c888a51342a1ae8b397f9bcabd2a21359d15d13ec18cb81301d9ec2c2d53`；疾病通路关联 ID `3e32439d8580cbb23b2d3f8fd7070bde45552a35e82a32e9fccc56ec8dfb15ff`。
- `HDAC1` → negative regulation of gene expression, epigenetic (`GO:0045814`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `c7544f0d24e56e97c52bc78d6d1e0c67308af1ac1d93d1ddfdeb6bfebbc35121`；疾病通路关联 ID `b5d2b6d4580762a5478db2da852a72463404c8c7d0cfc90bb243d5aad0474233`。
- `HDAC1` → RNA Polymerase I Transcription (`REACT:R-HSA-73864`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `53f5f0ac159d5d167889280ffe76fd75607198fee6a6d56fbbf70a7e7b7b893a`；疾病通路关联 ID `e06c48ae47bda9f2327284eb219e0178ce456f9f79ebe153f8c7ba235f7d8310`。
- `HDAC1` → epigenetic regulation of gene expression (`GO:0040029`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `b034527dff2eda8966e17363e6f1a0192f19abc13ccfdd4e2a8073307942e59f`；疾病通路关联 ID `d1fc8b4ff5a5b3f39295e793669ba8412852071864e6daa847c277f7deda642c`。

当前 S1 富集摘要：肿瘤上调侧突出 DNA replication、E2F/G2M 与 estrogen-response Hallmark；肿瘤下调侧突出氧化代谢、呼吸链/oxidative phosphorylation、脂肪酸代谢等。富集与路径重叠仅为注释关联，不是通路因果证明。

## 独立验证、机制假设与冲突证据

- Exp010 独立队列同条件排名：26.0；外部 S1 条件级排序与主排序总体 Spearman=0.544，Top10 重合仅 1/10。
- PRISM ER+ 平均敏感性：2.1834272844634444，细胞系数=9.0；PRISM 相关性弱且没有显示 ER+ 选择性，不能作为 S2 药效确认。
- 候选机制摘要：图谱记录 HDAC1/2/3/8/11 关联；HDAC1 在 S1 上调，相关 S1 路径涉及染色质调节和雌激素依赖基因表达。属于表观遗传机制假设，尚无 ER+ 乳腺癌因果验证。
- 文献链接：[https://pubmed.ncbi.nlm.nih.gov/28276480/](https://pubmed.ncbi.nlm.nih.gov/28276480/)；[https://pubmed.ncbi.nlm.nih.gov/18413790/](https://pubmed.ncbi.nlm.nih.gov/18413790/)。
- 本项目用确定性证据模板整理解释；未调用 LLM 生成本候选机制正文，因此不把模板内容标为 AI 输出。

## 局限

该药主条件仅由 1 条 LINCS signature 支持。WTCS 是表达逆关联，不等同药效。靶点关系与机制文献可能来自一般药理，不代表在 ER 阳性乳腺癌中直接成立。当前图谱没有可审计 PPI 边；不推断一层 PPI 扩展。后续需要多签名/剂量的重复、ER+ 模型剂量反应、正常细胞对照和机制实验。

## 可追溯文件

- S2 原始评分：`results/final_signature_scores.csv`（signature ID 可检索）；候选证据：`results/final_top10_evidence_matrix.csv`。
- 图谱关系路径：`mechanism/top10_mechanism_paths.csv`；原始图谱查询结果：`mechanism/final_neo4j_direct_targets.csv`、`mechanism/final_neo4j_s1_pathway_links.csv`。
- 逐条引用登记：`mechanism/top10_evidence_citations.csv`。
