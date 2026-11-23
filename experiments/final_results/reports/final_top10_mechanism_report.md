# Final03 Top 10 机制证据包

## 解读边界

Top 10 顺序来自修正后的 S2 WTCS 主实验；本报告不按图谱覆盖度、文献数量或 PRISM 结果调整顺序。WTCS 是表达逆关联，不代表药效。Neo4j 靶点/通路是来源数据库关系与本项目 S1 的可追溯交汇；对无精确结构映射的药物，只记录外部文献机制，不把名称相似视为图谱映射。
直接靶点 COMPZ 是 LINCS 目标基因转录量方向的描述，不证明药物与靶点结合或抑制。当前 Neo4j 没有可审计 PPI 关系，未扩展 PPI 层。

## 按 S2 排名逐药解释

### 1. ponatinib（BRD-K44227013）

- S2：WTCS=-0.5167，1 条签名；24 h 合格剂量中 5 个条件，20% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 125.0；PRISM ER+ 平均敏感性 1.0327045557973333（9 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：exact InChIKey；直接靶点 21 个；与 S1 显著差异基因相交 5 个；target→S1 pathway 关系 131 行。
- 潜在机制/证据边界：Neo4j 精确 InChIKey 匹配；ABL1、FGFR/KDR/KIT/SRC 等直接靶点中有 S1 差异基因，部分靶点连接到 S1 Hallmark/富集路径。可提出多靶点激酶信号假设；不同靶点的 S1 方向并不一致。
- 外部机制来源：[机制文献 1](https://www.accessdata.fda.gov/drugsatfda_docs/label/2020/203469s032lbl.pdf)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：0d4e5629591f626cfa57481d6ad016fbc4a82cb79c7fc0670685be9ca6b69a32; 16fef9ab278518564dfff7bb2d144d0f7ff23c15870ba5e2d446329ba1d5f2f7; 1a71230668cc79a4511638fac202f76d1dca1e1689e69f3086e96ff0875b32b6; 1f45172e7e3e13a2c3f844af60bae88f2d00c21c8e9c0c3069ce5a79da210f34; 3964251840d8d13ffd8733b56af1e374526996cab44a8c2963a5eefdb978da67; 50792ab995446317e6a2698163589cebd12c078ceafb768d127cce09a56a8224; 55ff687274961b38970eb6f977ebc955d4a4bbaa43c2a4050be7834e73e45d14; 60254e7e98264f0cf57302346fa48af5b0896a5ef85599aa3b792325f4ce0966; 833050136f8ac241579c6833b659302e0afbd086e5361c2271618e24afb1d4ed; 84380db1a973439a402c4d78ee92f7386f999b1d00441c10b8de3153fdec1cf1; 8f2b755c98bb160ca264d71921093dbfa90d73c6a1edfc45fdf8b85c998e292e; a1855e5a5c0965181238234049d5cd11f149f258b6d2bbbb079e5ac09c1cf6d1; ae2cddaa0d404a7ed81af5e26f68425e659022a86d807e344b311e288249361e; b49df7e902615377346646b29d5ff04b29bc92f5cbd70a9232c3fd4dd214461d; b85a2ee236b23c704b321f003751fbfb872993c24e9d723ca2d87e665ea5694d; e4e2002fc24e4240eb3beee0bee2c519678fd5b8e0445648eb8911a0e585ebfa; e5dd136213c3598a9d0d224986c3c3ef68bd4c12d2740895a8274e4e2d0017d8; f2018a13b0c9e438b9152e97737fb3dcdd6f87b81df9ef49eb68b802ad8acb35; fbd7a80b5249a072fd0b63d1ed909224edea9457040bcdde8820304330b336e8; fc2dbb4123cdb4da1c9bcceee031486bf861adc012fd65d6ce052fc7caff9266; fdd49cf7663693b77198a4f46ffd22f32d39b295861d61bdf670bf255c2be8e3。

### 2. mocetinostat（BRD-K16485616）

- S2：WTCS=-0.5059，1 条签名；24 h 合格剂量中 6 个条件，67% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 26.0；PRISM ER+ 平均敏感性 2.1834272844634444（9 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：exact InChIKey；直接靶点 5 个；与 S1 显著差异基因相交 1 个；target→S1 pathway 关系 37 行。
- 潜在机制/证据边界：Neo4j 精确匹配；HDAC1/2/3 等靶点连接染色质调控、雌激素依赖基因表达等路径；HDAC1 在 S1 上调。与表观遗传调控相关的机制假设可追踪，但不能据此断定乳腺癌治疗作用。
- 外部机制来源：[机制文献 1](https://pubmed.ncbi.nlm.nih.gov/28276480/)；[机制文献 2](https://pubmed.ncbi.nlm.nih.gov/18413790/)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：27730fe8fcc8d1fb1d5f67982ee4ce2ad4b2427cf8a2d78e34dd0187495f4c9d; 3b5ab53e8a33331ae2064f31b55b490d879e8d23e15df515fa253a63222ca9ec; 5287e6deb3b2093e54b83c44397c5cbee5ed5ed2eb2c642cccb987decb747fe4; 99bca6f28a0cc98506c69cb3c4ca8fd3913bba5108c408fa429deb210e0aa19c; 9d1ad02de8ffe6b1351484925bcd52c2c18e4fcfcd4036023a06f40361d450a7。

### 3. MK-2461（BRD-K56405753）

- S2：WTCS=-0.4841，1 条签名；24 h 合格剂量中 5 个条件，40% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 NA；PRISM ER+ 平均敏感性 NA（0 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：no exact InChIKey node in current graph；直接靶点 0 个；与 S1 显著差异基因相交 0 个；target→S1 pathway 关系 0 行。
- 潜在机制/证据边界：当前 Neo4j 无精确 InChIKey 映射，故该图谱不提供此候选的直接靶点或 S1 路径证据。外部原始研究报告其为 c-MET/MET 激酶抑制剂；这是一般药理依据，不是本项目 ER+ 证据。
- 外部机制来源：[机制文献 1](https://pubmed.ncbi.nlm.nih.gov/21608528/)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：当前 GraphBuild 无直接靶点 Evidence ID。

### 4. doxorubicin（BRD-K92093830）

- S2：WTCS=-0.4672，1 条签名；24 h 合格剂量中 6 个条件，83% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 352.0；PRISM ER+ 平均敏感性 3.1106043918433333（9 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：exact InChIKey；直接靶点 31 个；与 S1 显著差异基因相交 9 个；target→S1 pathway 关系 105 行。
- 潜在机制/证据边界：Neo4j 精确匹配；图谱记录 TOP2A 及多种代谢/转运关系，并连接 DNA 复制、细胞周期等 S1 富集路径。TOP2A 在 S1 上调。它的普遍细胞毒性不能解释为 ER+ 特异机制。
- 外部机制来源：[机制文献 1](https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/050629Orig1s033Correctedlbl.pdf)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：311dba9d91bad3e337560b4dbb4a76ab496565939bd58458007df0da04b9efd0; 3febd2a6e2a89c74a459d109303f60f6138ae73440921fab17a7b9ef3ede25f2; 40f07e2865c2a6ae24c43fb8e233201ae40ac9be2be36ef8bde8aa52685a5b20; 465c69940730e1f0ffcbc10fc8eb38c6636535580af64bd4e2bb759e52b4e256; 48d71fcd936c3e74dda9c19d81431b3b1ee513aa86ed6694b90fdbad71b4745f; 4f20c2804ae6d7737a1f965ba4891411703db2ebb6478f947ab43c0fdcb4d212; 525307dc6f59555208bfad8a989a1e3a3a7c3bc2d57d64f24b9950085307d3cd; 5d997674034af750148403cb1ed2dc913d2b6f0494a2d893b0f755a65e480c89; 6413b0d1dee52d9434de9bfe4aaa1ef94dc9d63b6269868966accce268428694; 688e5107fe81c66fc5e2a6d5700f390bb4125993a2aa933574f1dac293c30e32; 71a826b87bdaf7aa95c251934e5623db2ea8a86e8666e47aee4cbd8c0b2b1912; 80e72159fe781af66bebb5f7c2ca912ceb3cf216fb346d55b71f7b4cae747b30; 85d5231e7b35e388c29ee5a69486c329437e8417106a9ca30b64a2a055d4310d; 8923537aa63326cfa7a50112d476d4b9784f9e596a064ad8ab6837e74818be08; 91bbe08e4933b0f6bdd66f6a55f2f3379420623b3a525f61eeee66fff89a0a17; 99d99233aee268e716549ce9e4964f6637272019f77131152664a62e1983dc31; 9bb6849862f8f9db1faad49b26ea7069e3c14306c84c00a676d2beb4642aa7e0; 9d28f0d3b9dad4dd67b8b65eb4281fb7cba2749c1c083639970f71d2891515d4; 9d9762a5d03bd180d891bfec49834fbd4db75a9da731a44d5a8cf344fe7e4106; 9ddb39eb0bbc2a141d412d1ed3f0ef480ad380de991df5c7b353b0c982878f65; 9f9588c13e4fd3b29bf3972cd2b62947df35c6c93b6359800901a2422b10acd0; a1ceaa6093b6a2df8982e252e9ff5255cc8a8437d032585a05521aa0a8d87681; a827ebfec180c1e604a8489cb6d86cb2645aec6e9924f2ee3ffc41f445d4921a; ac16d0f0102fabcd86e92625d5487af15f971e7050204a30fd8047e116398277; b2a7d7217123bdbf9a7ffba792c873d98dd373487c8c757afc6d09b6e96713eb; b9423bf477d3758fe62bd524b7f3deee4ff561035e5b5e1c2390d6294f5b9f7f; cce3978a813f6b777d21ca589a2b4efe95db2c34411de6def1661f6e705a7319; d7c42225a47d3987c1053c62a9efd375f520a19427471d1804afe8b0ab174207; e4856c6760a1418bbd7127776dcef96880305c151f74d51237964a83250d0be6; e7afc919c3c345016fc1006cbaf359fc0fba8d9724ea47e4a2fbd5dfb2287a3d; f739d1216d7185826095f0152245c89d3ea5d25ff52881e6749a9b856a5a63d6。

### 5. rebastinib（BRD-K76694128）

- S2：WTCS=-0.4578，1 条签名；24 h 合格剂量中 6 个条件，50% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 NA；PRISM ER+ 平均敏感性 NA（0 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：no exact InChIKey node in current graph；直接靶点 0 个；与 S1 显著差异基因相交 0 个；target→S1 pathway 关系 0 行。
- 潜在机制/证据边界：当前 Neo4j 无精确 InChIKey 映射。文献支持其为 switch-control 多靶点激酶抑制剂，涉及 BCR-ABL1、FLT3/TIE2 等；只能作为外部药理机制背景，未在当前图谱与 S1 建立可审计路径。
- 外部机制来源：[机制文献 1](https://pubmed.ncbi.nlm.nih.gov/21505103/)；[机制文献 2](https://pubmed.ncbi.nlm.nih.gov/27927766/)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：当前 GraphBuild 无直接靶点 Evidence ID。

### 6. PHA-767491（BRD-K50000283）

- S2：WTCS=-0.4564，1 条签名；24 h 合格剂量中 6 个条件，17% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 NA；PRISM ER+ 平均敏感性 NA（0 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：no exact InChIKey node in current graph；直接靶点 0 个；与 S1 显著差异基因相交 0 个；target→S1 pathway 关系 0 行。
- 潜在机制/证据边界：当前 Neo4j 无精确 InChIKey 映射。文献支持 CDC7 抑制和 CDK9 共靶作用，分别联系 DNA 复制起始和转录/MCL1 调控；当前工程没有候选特异的图谱路径或靶点表达证据。
- 外部机制来源：[机制文献 1](https://pubmed.ncbi.nlm.nih.gov/18469809/)；[机制文献 2](https://pubmed.ncbi.nlm.nih.gov/21768328/)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：当前 GraphBuild 无直接靶点 Evidence ID。

### 7. iniparib（BRD-K11153516）

- S2：WTCS=-0.4553，1 条签名；24 h 合格剂量中 4 个条件，75% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 155.0；PRISM ER+ 平均敏感性 0.2234544371641（9 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：exact InChIKey；直接靶点 1 个；与 S1 显著差异基因相交 1 个；target→S1 pathway 关系 40 行。
- 潜在机制/证据边界：Neo4j 仅记录 PARP1 的一般 TARGET 关系，没有 INHIBITOR 断言。PARP1 在 S1 上调；但原始研究指出 iniparib 在完整细胞中缺乏有力 PARP 抑制证据。因此不能将此候选解释为已验证的 PARP 抑制逆转机制。
- 外部机制来源：[机制文献 1](https://pubmed.ncbi.nlm.nih.gov/22291137/)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：a432a020e64f0128551066b50f61682f0b9f900003e8c51b22b90f1b671e8385。

### 8. balaglitazone（BRD-A00147595）

- S2：WTCS=-0.4527，1 条签名；24 h 合格剂量中 3 个条件，33% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 40.0；PRISM ER+ 平均敏感性 0.11547362867406667（9 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：exact InChIKey；直接靶点 3 个；与 S1 显著差异基因相交 1 个；target→S1 pathway 关系 82 行。
- 潜在机制/证据边界：Neo4j 精确匹配，记录 PPARG 部分激动作用；PPARG 在 S1 下调，关联脂质代谢/脂肪生成路径。S1 方向相反并不证明激动剂能逆转疾病状态，需作为机制假设而非支持性疗效证据。
- 外部机制来源：[机制文献 1](https://pubmed.ncbi.nlm.nih.gov/22372600/)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：71209243e297d323fb3ce417629b53ceee656c8cdbbb03f79fcc420e6310248a; 829f55ab30c0f2410ede541472e99ae8b5807b52c51725996e0d91128c709d59; fba4167f822b4d3a96da791edea42fdeae960c2cf5e85eb5a6c1f31018fbe6ff。

### 9. PFI-1（BRD-K13094524）

- S2：WTCS=-0.4514，1 条签名；24 h 合格剂量中 4 个条件，75% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 NA；PRISM ER+ 平均敏感性 NA（0 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：no exact InChIKey node in current graph；直接靶点 0 个；与 S1 显著差异基因相交 0 个；target→S1 pathway 关系 0 行。
- 潜在机制/证据边界：当前 Neo4j 无精确 InChIKey 映射。文献支持其抑制 BET 溴结构域与乙酰化组蛋白相互作用、改变转录及细胞周期；此为外部机制背景，未与本工程 S1 建立直接 KG 路径。
- 外部机制来源：[机制文献 1](https://pubmed.ncbi.nlm.nih.gov/23576556/)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：当前 GraphBuild 无直接靶点 Evidence ID。

### 10. JNJ-26481585（BRD-K83837640）

- S2：WTCS=-0.4466，1 条签名；24 h 合格剂量中 6 个条件，100% 条件 WTCS<0。
- 独立证据：Exp010 同剂量排名 NA；PRISM ER+ 平均敏感性 NA（0 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。
- 图谱证据：no exact InChIKey node in current graph；直接靶点 0 个；与 S1 显著差异基因相交 0 个；target→S1 pathway 关系 0 行。
- 潜在机制/证据边界：当前 Neo4j 无精确 InChIKey 映射。其又名 quisinostat，外部研究支持 HDAC 抑制和组蛋白乙酰化变化；缺少本项目的精确图谱靶点及 S1 通路证据。
- 外部机制来源：[机制文献 1](https://pubmed.ncbi.nlm.nih.gov/27423454/)；[机制文献 2](https://aacrjournals.org/clincancerres/article/15/22/6841/74560/JNJ-26481585-a-Novel-Second-Generation-Oral)。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。
- 可追溯 Neo4j Evidence ID：当前 GraphBuild 无直接靶点 Evidence ID。

## 汇总

Top10 中 5/10 个药物在当前 Neo4j 有精确 InChIKey 药物节点；其中 5/10 有当前 GraphBuild 的直接靶点关系，5/10 有靶点到本项目 S1 富集通路的关系。未匹配表示当前图谱构建未覆盖，不等于该药物没有已知靶点。
多数 Top10 条目仅由单条合格 signature 支持，且不同剂量可改变 WTCS 方向；优先视作需进一步实验验证的筛选命中。没有细胞/动物/临床因果验证时，不能称为推荐治疗药物。

## 关键来源链接

- GSE70138 / LINCS Level 5 与本项目所有参数、文件 hash：`final_data_manifest.json`。
- Neo4j 精确映射、靶点、S1 pathway link 和原始 source_assertion / Evidence ID：`mechanism/` 目录下三张 CSV。
- PRISM 终点和实验设计：Exp011 报告与其原始结果；外部 S1：Exp010 报告。
- 逐药主分数、剂量稳定性和外部证据表：`results/final_top10_evidence_matrix.csv`。
