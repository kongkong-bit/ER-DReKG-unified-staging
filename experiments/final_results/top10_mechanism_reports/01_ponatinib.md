# 1. ponatinib EvidencePackage

## 候选与 S2 筛选依据

- LINCS perturbagen：`BRD-K44227013`；主条件：MCF7 / trt_cp / 10 μM / 24 h / distil_cc_q75≥0.2。
- WTCS=-0.516654；项目记号 reversal_score=0.516654；签名数=1；签名 ID：LJP009_MCF7_24H:E19。
- 历史 B200 置换经验 P=0.0004997501249375312，BH FDR=0.0039334146486079，置换数=2000.0。该检验只覆盖 Exp008 历史 B200 分析集；NA 表示未在该历史文件测试，不能当成不显著。它不是临床疗效概率。
- Exp006 历史稳定性：A rank=1.0，B rank=1.0，稳定性等级=low；可用 24 h Q2 剂量数=5.0，跨剂量负 WTCS 比例=0.2；限制=single signature。
- S1 规模敏感性同条件排名：A_original=1.0; B100=3.0; B150=1.0; B200=1.0; B300=1.0; B_matched125=1.0。全局结果显示 B100/B150/B200/B300 相对原始 A 的 Top10 重合分别为 8/10、7/10、4/10、3/10，故头部名单对 S1 规模敏感。

## 已知靶点和关系语义

精确 InChIKey 图谱映射：exact InChIKey；GraphBuild=`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e`。仅报告当前构建中存在的关系：

- ABCG2 (`ENSG00000118777`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `84380db1a973439a402c4d78ee92f7386f999b1d00441c10b8de3153fdec1cf1`。S1 direction=—; logFC=—; FDR=—。
- CYP2D6 (`ENSG00000100197`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `f2018a13b0c9e438b9152e97737fb3dcdd6f87b81df9ef49eb68b802ad8acb35`。S1 direction=—; logFC=—; FDR=—。
- FGFR1 (`ENSG00000077782`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `1a71230668cc79a4511638fac202f76d1dca1e1689e69f3086e96ff0875b32b6`。S1 direction=—; logFC=—; FDR=—。
- SRC (`ENSG00000197122`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `fdd49cf7663693b77198a4f46ffd22f32d39b295861d61bdf670bf255c2be8e3`。S1 direction=—; logFC=—; FDR=—。
- LYN (`ENSG00000254087`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `0d4e5629591f626cfa57481d6ad016fbc4a82cb79c7fc0670685be9ca6b69a32`。S1 direction=—; logFC=—; FDR=—。
- PDGFRA (`ENSG00000134853`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `e5dd136213c3598a9d0d224986c3c3ef68bd4c12d2740895a8274e4e2d0017d8`。S1 direction=—; logFC=—; FDR=—。
- FGFR4 (`ENSG00000160867`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `b49df7e902615377346646b29d5ff04b29bc92f5cbd70a9232c3fd4dd214461d`。S1 direction=—; logFC=—; FDR=—。
- LCK (`ENSG00000182866`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `50792ab995446317e6a2698163589cebd12c078ceafb768d127cce09a56a8224`。S1 direction=—; logFC=—; FDR=—。
- FLT3 (`ENSG00000122025`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `a1855e5a5c0965181238234049d5cd11f149f258b6d2bbbb079e5ac09c1cf6d1`。S1 direction=—; logFC=—; FDR=—。
- CYP3A4 (`ENSG00000160868`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `55ff687274961b38970eb6f977ebc955d4a4bbaa43c2a4050be7834e73e45d14`。S1 direction=—; logFC=—; FDR=—。
- ABCB1 (`ENSG00000085563`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `3964251840d8d13ffd8733b56af1e374526996cab44a8c2963a5eefdb978da67`。S1 direction=—; logFC=—; FDR=—。
- CYP2C8 (`ENSG00000138115`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `b85a2ee236b23c704b321f003751fbfb872993c24e9d723ca2d87e665ea5694d`。S1 direction=—; logFC=—; FDR=—。
- KIT (`ENSG00000157404`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `fbd7a80b5249a072fd0b63d1ed909224edea9457040bcdde8820304330b336e8`。S1 direction=—; logFC=—; FDR=—。
- FGFR2 (`ENSG00000066468`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `8f2b755c98bb160ca264d71921093dbfa90d73c6a1edfc45fdf8b85c998e292e`。S1 direction=—; logFC=—; FDR=—。
- BCR (`ENSG00000186716`): 关系语义 `TARGET, INHIBITOR`，来源 `DRUG_BANK; OPEN_TARGETS`，Evidence ID `1f45172e7e3e13a2c3f844af60bae88f2d00c21c8e9c0c3069ce5a79da210f34`。S1 direction=—; logFC=—; FDR=—。
- ABL1 (`ENSG00000097007`): 关系语义 `TARGET, INHIBITOR`，来源 `DRUG_BANK; OPEN_TARGETS`，Evidence ID `ae2cddaa0d404a7ed81af5e26f68425e659022a86d807e344b311e288249361e`。S1 direction=—; logFC=—; FDR=—。
- RET (`ENSG00000165731`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `16fef9ab278518564dfff7bb2d144d0f7ff23c15870ba5e2d446329ba1d5f2f7`。S1 direction=UP; logFC=0.879766560654955; FDR=0.0258332428159049。
- KDR (`ENSG00000128052`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `e4e2002fc24e4240eb3beee0bee2c519678fd5b8e0445648eb8911a0e585ebfa`。S1 direction=DOWN; logFC=-0.716671250126428; FDR=0.0147828263081773。
- TEK (`ENSG00000120156`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `833050136f8ac241579c6833b659302e0afbd086e5361c2271618e24afb1d4ed`。S1 direction=DOWN; logFC=-0.785058197008346; FDR=2.09464622896285e-09。
- CYP3A5 (`ENSG00000106258`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `60254e7e98264f0cf57302346fa48af5b0896a5ef85599aa3b792325f4ce0966`。S1 direction=DOWN; logFC=-0.462650972945128; FDR=2.98774963817148e-05。
- FGFR3 (`ENSG00000068078`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `fc2dbb4123cdb4da1c9bcceee031486bf861adc012fd65d6ce052fc7caff9266`。S1 direction=UP; logFC=1.63864339549385; FDR=1.19199778396194e-07。

## 靶点到疾病异常通路的证据路径

- `RET` → morphogenesis of embryonic epithelium (`GO:0016331`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `0e35a7219311e2d16c19719c50f6f6d53442c7a8e0f634ea25c6f6bb36a3aee0`；疾病通路关联 ID `c63b01d93fef7b8ddb30ee5a21bb3f8e7f46b166f3cc1a074125e190efca2f5e`。
- `RET` → epithelial tube formation (`GO:0072175`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `e1752b2edef2c62a41fbdfc724821982f2fc302b9cfeba9011413eee9363bead`；疾病通路关联 ID `d59646feafc8d6e55371fbcec669525dcc5f9f85e752ddf794e3404e28c4db6f`。
- `RET` → embryonic epithelial tube formation (`GO:0001838`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `7e9deec8b93bba32fbb8e6f58f01ce81846017df2e62d1d6facfeaf32ba7330b`；疾病通路关联 ID `1787f35dec5460baee5ddf5efda4fe73747b338bbfe126afb1cd4fd93fe68a6e`。
- `RET` → tube formation (`GO:0035148`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `3d2a04d2df3aa4e3c8e35d0e37b19da5afdba32167882ea001b9b50ddb5f9b4b`；疾病通路关联 ID `1bb167c6dc635a1dfa7a798f794d7e0af584487e4a3a853ec428db3cf7379883`。
- `RET` → HALLMARK_ESTROGEN_RESPONSE_EARLY (`MSIGDB:HALLMARK_ESTROGEN_RESPONSE_EARLY`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `9cb5e7fd05803f2852beba9fc8903b2ecf381be1c84e38a959c81eea710504b0`；疾病通路关联 ID `e483d9a23cb1600f58799dab9b966eb86dc1592858274c3458328aceea2aea83`。
- `KDR` → regulation of cell shape (`GO:0008360`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9c98e0f3140a6f114b3fe5d2818ed2bb3c8b678a33f01bd8158c0dc6e165584e`；疾病通路关联 ID `92cc961d46d1770b171fb0aa30b6e2ff1439aa62d6f0b943f4664c73ef67a9d2`。
- `KDR` → positive regulation of phosphorus metabolic process (`GO:0010562`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `03a916805431aaf797832af94c5f2aab6b7c7fd7de93a1b49a98d38cf09ecf5b`；疾病通路关联 ID `5432f1334ad6a8b5420a97403222337c97766ac08ee2e56057b6e9782fc0c732`。
- `KDR` → chemotaxis (`GO:0006935`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `97075265bf126516e72e76a23de9c6dd2bc9f80bc718a1888d7367a93fec7dce`；疾病通路关联 ID `4d3e55a8c19abea3e704f0b8242f32aafd49034d9e428e81f3f9292c46b14786`。
- `KDR` → cell-substrate adhesion (`GO:0031589`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `520a5b3fd6865ef61aa9afd935b29b353cf042cc8426146cfd0677bab37b341e`；疾病通路关联 ID `95ade602b2f0bb5b412f7e0476049ed0e4d54fa9bae80d8cc3bfcc303e847c94`。
- `KDR` → regulation of phosphatidylinositol 3-kinase/protein kinase B signal transduction (`GO:0051896`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9ee1b1c86da257fdb148d7f9f95c1829ebb1e9e2c7cce8ee9fa5b8a7d6fa85e8`；疾病通路关联 ID `c8dda60f68509c6827132708d86743b70fb9d52f5a2208406eb049cef50c91d6`。
- `KDR` → positive regulation of transmembrane receptor protein serine/threonine kinase signaling pathway (`GO:0090100`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `81b2a107e5d2dc56da5fec83317fc7c3401fefe435f98d78a2622ccee6f35638`；疾病通路关联 ID `8a6a991e4bdb1f4af64eb9dfe500395af2905de93fb80fd3383c916fe0f91b8e`。
- `KDR` → positive regulation of MAPK cascade (`GO:0043410`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `60ba89c08fcf64cd2f7dfee5383514ad73596af45633e03a2de958076ea30c15`；疾病通路关联 ID `8ce55eaeaf0760188164489a6201d81ca46446042d4a572adac050107b41062b`。
- `KDR` → skeletal system development (`GO:0001501`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `415819e4d8a514d59c2e84033a2352f997490b0b69c279850a6f5e7dabf2387c`；疾病通路关联 ID `50f5382410e83a7ce19de728fc8b21d4ec367566008b6984f60ea14d83be73f7`。
- `KDR` → regulation of ERK1 and ERK2 cascade (`GO:0070372`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `55f431ab726c87f0c7d91c2c87b2e15933306b64736d55351faf4753e7335ccf`；疾病通路关联 ID `a046b4934e291944afc88552bc501b4fde25e24f18d3f1ea536a9a396f2af097`。
- `KDR` → cell surface receptor protein serine/threonine kinase signaling pathway (`GO:0007178`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a9f08ed35bb228abbe80f441e4e91bb665c59359860f3f221dc746f70cf436d2`；疾病通路关联 ID `0512826138d0e040bdb3c83956e0027f9c592ceadcbdde541f61e189ce34a1d9`。
- `KDR` → respiratory system development (`GO:0060541`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `97d6b4c154d3400cfacce480bf0e6f5ca554db8b59afeb51189b9b5c1ff58eab`；疾病通路关联 ID `e884f9fafc7678cbf81890257c22f9bdbbfde5a97844738de9dac020ffd580e3`。
- `KDR` → positive regulation of nitric-oxide synthase biosynthetic process (`GO:0051770`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `225fe272e0e155197891db217cddfc0b0a3154c90fb702b993e2e7135ee1c300`；疾病通路关联 ID `4ebc9017504cf6be50450bdb18f8c40a258585a864d55cbbce1f8fffb1da69c3`。
- `KDR` → endothelium development (`GO:0003158`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `af727de2f05dd9e427922fe119a42c85ef68d774abff641b69a559f687b0c58f`；疾病通路关联 ID `484a78646dc307f0de7eedd53aee08095cdb7d725a875c3b5509137d404aeef6`。
- `KDR` → regulation of cell-matrix adhesion (`GO:0001952`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `3cf248a408939329fad4e5073d25f89c6e6e4d398a45eb75dd33854a2acc3981`；疾病通路关联 ID `7346ab5af3782583af7b04152e70eb5c1073d5d9e27b7448d5f425633d2a601f`。
- `KDR` → regulation of cellular response to growth factor stimulus (`GO:0090287`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c1c02889a1ed3feaa94a2e50e51ad626a95b4b8056ea3cf41a5d2dec7a3da83e`；疾病通路关联 ID `113d1608ed4f2fc5b8c99e2fd23ef1d95ba89da4c9c1fd90f1bdbd1a80763b63`。
- `KDR` → response to BMP (`GO:0071772`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f0e53c23edf79393d841646788df4ee6d52d50104942c7d097771ef844ebc5db`；疾病通路关联 ID `4400b08e35f9dc29cf4183008fa98d8bbd92121c0faa2ca536a1057a78dc7bca`。
- `KDR` → positive regulation of vasculature development (`GO:1904018`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d8e54ab917e5027ec2bcf39deb4cc2d6335203c09032702fc1431b01bf3ad462`；疾病通路关联 ID `e3c9577719724822b0140df2e839f0c4b54fd1761c1b2a25d1f84e97afa6f2dd`。
- `KDR` → regulation of BMP signaling pathway (`GO:0030510`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6427c707daa27c2feef7c1615619153614107fe41bac680c6589e68e12236248`；疾病通路关联 ID `e3b45c7d87f2362905bd0ab04ec0a4119e10502c0a1c05f4158326d4400b3dd0`。
- `KDR` → positive regulation of endothelial cell migration (`GO:0010595`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `70cd41d898e3b6d259e51b0fcb39b272e4a658b3069fcaa8641708dfe81d3c2b`；疾病通路关联 ID `b1e09aff5e23c5e6021da18a35ac2f6505b0da26aa8aaf3f2978a6fd7879996e`。
- `KDR` → cell-substrate junction assembly (`GO:0007044`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `33bee064861dfb22690a614641a3a0a0b93d324da8774b42a4c5c222ae178cea`；疾病通路关联 ID `0ce286d4f76abd67c1851042237ab6fc541601d0c3931392b7e97f0a7fea3b46`。
- `KDR` → cell-matrix adhesion (`GO:0007160`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `4f74ad9f610988f3c5cfbf0bce5bc28987a79b655156a11052eacf42db4005e2`；疾病通路关联 ID `24172e3eb7c553dc22fa03c1cb91ffd2dd8f56a37e8dd518f96460e010be716a`。
- `KDR` → positive regulation of ERK1 and ERK2 cascade (`GO:0070374`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0fda58d4a15e3fee1e2afde20cc0fe4cf4ed473fd4dabba979e0c8f154162ad1`；疾病通路关联 ID `e3886940e0e54af393fe021854dd46f0f08db6b7956955b9d8a55560064292a9`。
- `KDR` → wound healing (`GO:0042060`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e651aab4f92734bcdcb1645879b20f2c1ac4b733cdce1e220045e7e0c11babb1`；疾病通路关联 ID `65d248b22850e6a10bf2f8aab3db81986c63422a09c93bfdbace10642781baed`。
- `KDR` → regulation of focal adhesion assembly (`GO:0051893`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5fbf86d0965ef3711868871ab1fadea4b3fe0baedadbaa543c9e6232e880cb1d`；疾病通路关联 ID `4b73cdb2f630d014b3957a54b6303ba06c4e4f3375182c8fad616da3960bd452`。
- `KDR` → regulation of cell-substrate junction organization (`GO:0150116`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `13a0c304bbfa8501ac7713bebdc7b40ba6747a59fd4010e6fe7acff463467fd1`；疾病通路关联 ID `6dd9153bd4d99a7fdf6c75f7f4aa67bcbcb3055cf18331faf8dd8aaba61f6808`。
- `KDR` → vasculogenesis (`GO:0001570`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6968618a68e4a7e07426a9008633eb9abde81ddefb618216d89fba07d33025cd`；疾病通路关联 ID `e22547a5f87a9328464f6ae1177bb81b0e3241071c7d18f0856d4ca0c6296a1c`。
- `KDR` → transforming growth factor beta receptor superfamily signaling pathway (`GO:0141091`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `46c2e61daf8117b7b345165c398fee043a2ef1c51c0441206deace286e4449f3`；疾病通路关联 ID `bb5ee6294798345815a90c9a00515fdfcbc38a80a1b3bd3d094399c90e996959`。
- `KDR` → positive regulation of phosphate metabolic process (`GO:0045937`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6161529e320af7f097f6e83945ebe361ae9d9d5ebb35777dce2207bc4e54a5c7`；疾病通路关联 ID `50ef8cba9e20d70045137e4295d6d6e396726c51ac3626179b7c995818887d45`。
- `KDR` → taxis (`GO:0042330`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `aa6ce50ea90bbe857e04365589288f4ea614f02e1307ba2e9d4ca5f4c49e019f`；疾病通路关联 ID `0183c368ee2899fa14555eaaa0323cb70fae931922edb49b16d64a86180f0981`。
- `KDR` → lung development (`GO:0030324`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c5b0bfffef9405e179a4715a52fbad9367b2ac5f9b976ad49db3034f066edbf6`；疾病通路关联 ID `734c1a52399483e3c103012e2503e8b177ccc85f52a1f5a2765d4c8523dc8141`。
- `KDR` → regulation of cell-substrate junction assembly (`GO:0090109`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `435f336ddd039b5d2d58d6826080b9cd19b89ff00720a2e250e3a8048f52d725`；疾病通路关联 ID `4cd4b043a30ce37ff93a422853c7e762ccff528269c9d9e096e8270f678ce132`。
- `KDR` → regulation of endothelial cell migration (`GO:0010594`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `8a8f0131ad59a515e74369648a04a2eec2a75542983b20e11e0fee44dcc60b68`；疾病通路关联 ID `44b6f215656186368b386d7c2c0f0e740a25a47807f667e1b302c48e475df601`。
- `KDR` → regulation of blood vessel endothelial cell migration (`GO:0043535`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c0a8d1bbc0aaabcd62a25555dbf13a48f02b8c5f8e1389cd4ce088b70b3b8f8d`；疾病通路关联 ID `a60ac66d75840927ddefcec5a2adda1c2a6b78b133aa8ef5ec367af084e9331b`。
- `KDR` → cell migration involved in sprouting angiogenesis (`GO:0002042`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `52f4438f8b3a8859e06d29de989ce9183a7bb237f52e94d15dc02924409dc5ab`；疾病通路关联 ID `a987b3f45f55523207fbf6649320d8fe45d444b4160634faa03a4c99e3973189`。
- `KDR` → cellular response to BMP stimulus (`GO:0071773`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e16de70c399d72ca9af5879417196eb836cea15349f730ee494a3b6331f8e2a6`；疾病通路关联 ID `4509284f564dc5bed95017f62220dfb752bd29c18e5da4452cf5f2eee1abf049`。
- `KDR` → nitric-oxide synthase biosynthetic process (`GO:0051767`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `2834a24a0dfa81ae68ce6de04d6ee70fd6bf0f61ca60ff0379d7f6a88f4a8ad0`；疾病通路关联 ID `e04f6893f38dc2b9f8669cab5b44338974e8e8a19e16a7104eabc22084c77445`。
- `KDR` → regulation of transmembrane receptor protein serine/threonine kinase signaling pathway (`GO:0090092`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `58483473284655665dae7265feaeb195308dc7ec865ae7c19542b4beef648eb5`；疾病通路关联 ID `f66335b63e3f4b0c13e9d8cf21356787e0779f84d91a351e84e3c8b06627bab4`。
- `KDR` → BMP signaling pathway (`GO:0030509`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `2b0439f5b7a303457aa452c772ebea681315bfbbbd9d6ec6c7806fb38d806fd6`；疾病通路关联 ID `98e82478fbf47b9667d1cd742dc979364cedbba95e72c38fab962530ed48e2c4`。
- `KDR` → positive regulation of cell-substrate junction organization (`GO:0150117`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `439d9f3ea7840007c495971f071666d190d406038e87bd18ed7f501c981c356f`；疾病通路关联 ID `a753577a6eab89b3c82989df5c4c0521db63e28c7c08cf6ca3794ae089334559`。
- `KDR` → regulation of nitric-oxide synthase biosynthetic process (`GO:0051769`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f1ac91fca213c61af2c1dcee83a2cb6416410bc3534f440f17afb8af98b31f1f`；疾病通路关联 ID `5ed873cf1313b284c88573f490a23ec0cc8bc3edc49616a36503e7aae839c3cd`。
- `KDR` → cellular response to vascular endothelial growth factor stimulus (`GO:0035924`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `36cae9022364f59d1747896649a6baefa76ce8d0c433e24c945af9f3dad65ba1`；疾病通路关联 ID `4d551ec7e3d8f536fae41b09eab1dcf6215cd092baf1859d24ea3691aa4ee116`。
- `KDR` → positive regulation of vasculogenesis (`GO:2001214`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `25bce9ed2a5765ef9333813650eda189b8fb74ea1db1b7a5c9cbf51a518ff39d`；疾病通路关联 ID `1469865d7acec4e678feda2e1c502b0fd288e6c3ca7051e3ca80555f007cbbb6`。
- `KDR` → phosphatidylinositol 3-kinase/protein kinase B signal transduction (`GO:0043491`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `b9b36d659d0ed955ec0a35db43389852723d99372628acf48394587879589a84`；疾病通路关联 ID `735797c1792b4ab370d5d54545ccedd587b270fd734695d47b6abfb7f5260084`。
- `KDR` → mitochondrion organization (`GO:0007005`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `4240d57bb67e3e4c0732d82e6affeceeb29911916a0c130f06dd26c5d86186eb`；疾病通路关联 ID `91f16f83f9f1362d0c382e6ddaa2900ca7ab7efb03e0e19349590019a0bf952b`。
- `KDR` → epithelial cell proliferation (`GO:0050673`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6af17c5d721795318acf889e8501f2452d4a7b59c7bbc2ff23a05db335497f55`；疾病通路关联 ID `2b2df3c276167dd52de61de430ba76c64ad2ff635c0a1b927dea816368f76fc6`。
- `KDR` → sprouting angiogenesis (`GO:0002040`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `46324b9d0140f95686053f7fd8d19a096eaf3eedf3ba76abd19ac4544a000928`；疾病通路关联 ID `3a78b171a063e82335a997f1f74c6426ac750ba6b4546442e6ef03c5f3351285`。
- `KDR` → endothelial cell proliferation (`GO:0001935`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9fbb74e989630bb960b571117ad222269d492871debcaf0d66b6d2057e05cbb9`；疾病通路关联 ID `8dc81fc4823f3f86f28e823b0345ee0c22007bd07b558722838ff07ddfd6c651`。
- `KDR` → positive regulation of phosphatidylinositol 3-kinase/protein kinase B signal transduction (`GO:0051897`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d928cd3145a173e38947dcfc8c736ef00a6a104e720a38b9a68c1a8bcf18a73e`；疾病通路关联 ID `74fa5d3671ef01b7b0d3faf369a47905a580e0f60aa2cfe0167c209aa84f8fa5`。
- `KDR` → positive regulation of angiogenesis (`GO:0045766`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e80d5574c25a714617eb96fbad4d5e9f1087ede79b21020e94fe944f1a43927e`；疾病通路关联 ID `651d6c410b4d984475631560930a513618377c3828bdf195e684a378448add03`。
- `KDR` → blood vessel endothelial cell migration (`GO:0043534`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `67a718bdf0ae1c63f3bef64a83037133a9ddc744ce976680bce0938ede901a52`；疾病通路关联 ID `50ba80f9b9af0d7dce2b118c3a9a569cdfb3cfc31d71b4a121923ccb9f4752fa`。
- `KDR` → cell-substrate junction organization (`GO:0150115`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `8c6a920451b5916543009695259f346db6a48b40cd0feec732b78eadbacb62b8`；疾病通路关联 ID `a4dbe8075d8d617b6fbb17ae5fefecc1f5e5bba538303313e03ed1d606f503d6`。
- `KDR` → ERK1 and ERK2 cascade (`GO:0070371`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a87e490c5e842f51961f7e86b3e7cab4b80e7a839b8d33271050dc40a4f1f4ed`；疾病通路关联 ID `2a55de0b79e4f984615e2510f175f9aa78362954260852b32ab07892cc1ba252`。
- `KDR` → regulation of angiogenesis (`GO:0045765`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `040a1f6e066e48255b15f29f3b71cbf3eb51ea25d94c782c3b83516babec4dca`；疾病通路关联 ID `fd621a9075548c5edd7a1681b2b92bf81e1b72ac77bf76a96f9b0280943b5816`。
- `KDR` → regulation of cell migration involved in sprouting angiogenesis (`GO:0090049`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e81df8f76e3b993917c44a04b0b776625ba5c329708b9a9b52ac0b76f0711c94`；疾病通路关联 ID `7d1dfd8f8a54895d427b2859d414e80f24ee21e55f5a73eef1f364504947be17`。
- `KDR` → endothelial cell migration (`GO:0043542`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6c0d54d86cd8c6705b0d2e659b6f9fd0c47eac6bc8d2ef92abb958b9703d1d94`；疾病通路关联 ID `2ee8a37378e48094801869aefeb77dac866b40b9e651f16e2005473c5205dc00`。
- `KDR` → mitochondrial fission (`GO:0000266`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6c93df7b6fcd4beb27158f9775f18573ee0842396696a9052c55ff55f53961d2`；疾病通路关联 ID `c3021057f085ec4f670f9bf488f2f1705c4f91f74ff6eccc6d0d25b78c77a7b9`。
- `KDR` → regulation of vasculature development (`GO:1901342`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0b62781aa4f1cba2ac18125b77318823e786febbc094edf26f47a56e1845d345`；疾病通路关联 ID `9822982fb9d290e1803fc82c30295bd6540ff3821fbb14ec3957f5a4530dfc2b`。
- `KDR` → respiratory tube development (`GO:0030323`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a19d6e49b808cfd53a827dfb32fd9b0c9a98c03985c10bcfe436d94e533e8bd8`；疾病通路关联 ID `46f95add7f8231f9b9ca652d23e050bad5e9401f172daabd3b68d02378f31398`。
- `KDR` → focal adhesion assembly (`GO:0048041`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `77bbe2e5bbd4688fa8ce7b7ef300e5a216f921feae7d5ea6930764caaabc5943`；疾病通路关联 ID `3451993a8ac7788d299e5e84522f188e6dabd85aad3b4763d4e93ee3e181c8de`。
- `KDR` → bone development (`GO:0060348`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e1284931e86775e0b1ebea279f595b7663dd158a1b0c0a1f01efe3df33122d6b`；疾病通路关联 ID `6a6cab98440e954614c24d428dd0713bf5d322e48beb044a8c5559df82faceab`。
- `KDR` → endothelial cell differentiation (`GO:0045446`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a7e02f242f9059f5b094b24d42152821cac1b2b45758b73ae7bee02af64f113a`；疾病通路关联 ID `d11257bb799a39776658382a54c78f56048e47ef523d298e5f8708428b08cef4`。
- `KDR` → regulation of cell-substrate adhesion (`GO:0010810`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `559438b93903b8383bbbc0f5658598c081cbf564b2b4a6b81d38f1674539e212`；疾病通路关联 ID `d5407a00354a8168e47d0941c6d8a36b0e199c033c8108b1a55c2c90c52799ef`。
- `KDR` → regulation of cellular catabolic process (`GO:0031329`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `7e89854f9b3210fc348b0c0ef4706ed8f35cd4abe4cb2155d09b5e662415db16`；疾病通路关联 ID `60fffac54ef0e96afcb255f0bfded1c080a8f9bb433d21145cbe8579e36cdf8f`。
- `TEK` → regulation of phosphatidylinositol 3-kinase/protein kinase B signal transduction (`GO:0051896`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ce35068a618bd9dc4721cd4112930880c0ce858ac48c9cac182b2c973fa0c919`；疾病通路关联 ID `c8dda60f68509c6827132708d86743b70fb9d52f5a2208406eb049cef50c91d6`。
- `TEK` → response to purine-containing compound (`GO:0014074`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `1faabac6ba9bdc9117ac46f2b6cd3a81665968c5284c495440ff66a45e1300d0`；疾病通路关联 ID `caedda04d68b8d75f35030701ae35364c96b52e40a58382d3aafa119261f0f27`。
- `TEK` → negative regulation of blood vessel morphogenesis (`GO:2000181`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `837880cedc3103c3653ca5fdf89d776855c705008bfa3ff63fc13fa37cf69bb5`；疾病通路关联 ID `26fd9ee0347ea6811506ebfb1dfb6050fd7e44d3eb0bb034403396fad8683520`。
- `TEK` → response to oxygen levels (`GO:0070482`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6f425ac1bce8f1199210aec4bdc80362c59d0cd6154891f33dbbcf88906f50da`；疾病通路关联 ID `0a45db29ea5d5f68ddb395bdbe994b8fb5fed8058986287b6a199c31c140a8a4`。
- `TEK` → response to cAMP (`GO:0051591`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `42abcd840ada793a9ea2a5a9b9db99ddd9e4e2f8469d042858905555a79898c8`；疾病通路关联 ID `11bb71c833dee90da8b8948ad8874520af4159fbdfa06883c37551dfa5d2bab0`。
- `TEK` → ossification (`GO:0001503`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0ada580df9bcf5549ed3d8bf334293af52162321f65604cfbd3e97c01e36ee45`；疾病通路关联 ID `808aa65462f43e4d91520ce6a337ba106e9180d2bb8fa1057377de329d82cd96`。
- `TEK` → regulation of focal adhesion assembly (`GO:0051893`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `3387523132ccd54966a8c18b549fa4221f5c25b3309548d5cbfe2f7c52836119`；疾病通路关联 ID `4b73cdb2f630d014b3957a54b6303ba06c4e4f3375182c8fad616da3960bd452`。
- `TEK` → cell-matrix adhesion (`GO:0007160`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d99475fcbe30a6b87990469c16129a36bb5ce5e14f3b681c62964c0c3007936d`；疾病通路关联 ID `24172e3eb7c553dc22fa03c1cb91ffd2dd8f56a37e8dd518f96460e010be716a`。
- `TEK` → positive regulation of MAPK cascade (`GO:0043410`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `54e5cd3be82283c5fc034b6dc5be5833667bdf42041d5ce5e7a4606412ab1f70`；疾病通路关联 ID `8ce55eaeaf0760188164489a6201d81ca46446042d4a572adac050107b41062b`。
- `TEK` → bone development (`GO:0060348`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `97d0bbd149ea7aa3a1936296f1ceecf34bd041cb565931e5992a229f79d6feca`；疾病通路关联 ID `6a6cab98440e954614c24d428dd0713bf5d322e48beb044a8c5559df82faceab`。
- `TEK` → negative regulation of angiogenesis (`GO:0016525`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ea349c01f66e10acc47e09224742a1187da2fd42440e9e939b31747d5a4c3ef3`；疾病通路关联 ID `329f3715efc912c868c20f9da5e285ef19df0176f2d35ebe1a15d2560b21d42b`。
- `TEK` → negative regulation of response to external stimulus (`GO:0032102`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `50a24239c2093d2294f64579883837c2d309e695193461354735dd413f6aa721`；疾病通路关联 ID `ce602b69bb0f10967100d2c27ad49a7c2dc3f32a049ab21cae52a478dc87ea6b`。
- `TEK` → endothelial cell migration (`GO:0043542`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `4cb41498ded289d73a0bce0cfe02df46dd1e91e4d12f0c757196ff5203d7c175`；疾病通路关联 ID `2ee8a37378e48094801869aefeb77dac866b40b9e651f16e2005473c5205dc00`。
- `TEK` → response to organophosphorus (`GO:0046683`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `692a0d895395ef0b76bb4733b78d91cd95eeafce4d07f9b9292c3405255c73d0`；疾病通路关联 ID `eb1d33f17acc1e3b9a6e66d50703a2dd89fa3195744052bb4e6a01096e7590da`。
- `TEK` → cell-substrate adhesion (`GO:0031589`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e61bdee41ad56c00f7b1328abf0c1dfd0850d56d34a3377ca5d2441198842d0a`；疾病通路关联 ID `95ade602b2f0bb5b412f7e0476049ed0e4d54fa9bae80d8cc3bfcc303e847c94`。
- `TEK` → positive regulation of phosphorus metabolic process (`GO:0010562`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `709456bb85c0b38dc7fb97bd3e1eb339b47db080361b511c43ec3b38f13b4288`；疾病通路关联 ID `5432f1334ad6a8b5420a97403222337c97766ac08ee2e56057b6e9782fc0c732`。
- `TEK` → positive regulation of phosphatidylinositol 3-kinase/protein kinase B signal transduction (`GO:0051897`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `819f1e6a47bbe0ca5f414d602b07e9cafa1ded9b7eeef17bd9a0b134f169f9fa`；疾病通路关联 ID `74fa5d3671ef01b7b0d3faf369a47905a580e0f60aa2cfe0167c209aa84f8fa5`。
- `TEK` → response to hypoxia (`GO:0001666`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f819f112ff93505866645e1824f4618007e744f6994c4b9a2999588da382f6e1`；疾病通路关联 ID `f09d1eae7bc189a820971f26a6b7b752908b443169a15fe7708d6fbbbebba181`。
- `TEK` → renal system vasculature development (`GO:0061437`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a6851d513d4b5a7bd45507cf1994e3622840c4897bb811734450938ac137f981`；疾病通路关联 ID `df35cd1d4fb4325cc38b98b829ccd3e791cb588fbc8c57a6ec4706ce01fd3867`。
- `TEK` → positive regulation of vasculature development (`GO:1904018`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `64f5a9ad1d902fd8160b7843ad29827df0e47591e5137b0f4c421ac344b800ab`；疾病通路关联 ID `e3c9577719724822b0140df2e839f0c4b54fd1761c1b2a25d1f84e97afa6f2dd`。
- `TEK` → kidney vasculature development (`GO:0061440`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `1a9df4f95836eddecc28d0310cdf43337e9b2a5de9b6b04bf1b83e1e49bf28f2`；疾病通路关联 ID `bbc0d5d911df74522e78370b6fd3aa690588afb405ab81cfc8a69309c8b75d1a`。
- `TEK` → regulation of cell-substrate adhesion (`GO:0010810`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c500ced0e8b49dfca9f42c6f1d4c3bc62469f5b8d53c052a6cbe6abdf703a3c2`；疾病通路关联 ID `d5407a00354a8168e47d0941c6d8a36b0e199c033c8108b1a55c2c90c52799ef`。
- `TEK` → focal adhesion assembly (`GO:0048041`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e86c55d0cb6250a66363a8e1615f09528d98003fce53282b5c25c0d5fcace4c1`；疾病通路关联 ID `3451993a8ac7788d299e5e84522f188e6dabd85aad3b4763d4e93ee3e181c8de`。
- `TEK` → response to decreased oxygen levels (`GO:0036293`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `bb06b1f1307eaffc9c840bd8be34e36692b210b54850c2fd0bce883cc85f63f2`；疾病通路关联 ID `bff18f6e7b48c048d68d23df1a3bb5e1d31044fae3f22719806a1c5ad2fc07e5`。
- `TEK` → ERK1 and ERK2 cascade (`GO:0070371`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5e25f00f7a18cf5177596753e9974790e69d47f0bafd1db2da5fab6e61e468c0`；疾病通路关联 ID `2a55de0b79e4f984615e2510f175f9aa78362954260852b32ab07892cc1ba252`。
- `TEK` → skeletal system development (`GO:0001501`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `1494d2571847448b92204626fec155ae60a533fd2e75f32a34030bdd458d2542`；疾病通路关联 ID `50f5382410e83a7ce19de728fc8b21d4ec367566008b6984f60ea14d83be73f7`。
- `TEK` → sprouting angiogenesis (`GO:0002040`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `2067372fbcc5b92f344ca640ffdbf946dc08c3c9b7087cf17e1761d2f6d151d9`；疾病通路关联 ID `3a78b171a063e82335a997f1f74c6426ac750ba6b4546442e6ef03c5f3351285`。
- `TEK` → vascular process in circulatory system (`GO:0003018`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0967b9d65d04a6063d0c40e74c63d4ecae8b4820b98d8498cdae39546013b146`；疾病通路关联 ID `dadb1cf9ccdeb19c2a014578f2f8e620e439646304d40061ba4d74009d0c8808`。
- `TEK` → positive regulation of ERK1 and ERK2 cascade (`GO:0070374`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9ad99a12c24aafb5427aba9aa04e54d2fd59409e3111abd4431ef9910defab19`；疾病通路关联 ID `e3886940e0e54af393fe021854dd46f0f08db6b7956955b9d8a55560064292a9`。
- `TEK` → regulation of angiogenesis (`GO:0045765`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `2879a98fde5f9baaa2127ddf16bbb8ab742434af92c1d6daf2a0d21ed35291b9`；疾病通路关联 ID `fd621a9075548c5edd7a1681b2b92bf81e1b72ac77bf76a96f9b0280943b5816`。
- `TEK` → small GTPase-mediated signal transduction (`GO:0007264`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `1a1310db84da281100a597566587037e9500a811fa2b7b923c0a40c943b0f2c7`；疾病通路关联 ID `e6a875d8415f60e03ecbc60fd57f7bbbe382a4abd1ecf1cb6c811b74afd36e24`。
- `TEK` → blood circulation (`GO:0008015`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `89ecfc8ef6ce5be88e799e39d1b05c9b4afc5b8e995aa6fb7905c30b4b00c589`；疾病通路关联 ID `0bbba9e3e486b38c84c1f45032a5d0ba8f00a6fcc16ecebf9073058fe2508811`。
- `TEK` → substrate adhesion-dependent cell spreading (`GO:0034446`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `bbcb528763bf37a6261953e0b9f3649a5098d867c70bfb774c311c5b35e528a0`；疾病通路关联 ID `68c45cf82bbfee7a1d922bf235b45d9aba8492a7bc48ab2e4ab822d950e3ab6e`。
- `TEK` → positive regulation of angiogenesis (`GO:0045766`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `59635e766cf25d7405aa17f3599d4a3e85bea80dde6b7880b3c190f7258e0587`；疾病通路关联 ID `651d6c410b4d984475631560930a513618377c3828bdf195e684a378448add03`。
- `TEK` → Rho protein signal transduction (`GO:0007266`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `1c8cb97559472b657373ebf4b08109961f43c9bd6c937913caaac092c0044419`；疾病通路关联 ID `4f22b8c6e58f0fc7f137cc951a71ed197fa38dad52245b0106c5cfa9fe1f7224`。
- `TEK` → positive regulation of endothelial cell migration (`GO:0010595`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `3dc86fcea1b829fee27e2e1c58ce415a9f5e059f84e3bc1133318cb9522f7fa7`；疾病通路关联 ID `b1e09aff5e23c5e6021da18a35ac2f6505b0da26aa8aaf3f2978a6fd7879996e`。
- `TEK` → cell-substrate junction assembly (`GO:0007044`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `4303b12d1af1a8b67981426bc64cfd5a3b5384a7d65db12cd2357c455b147ca7`；疾病通路关联 ID `0ce286d4f76abd67c1851042237ab6fc541601d0c3931392b7e97f0a7fea3b46`。
- `TEK` → regulation of ERK1 and ERK2 cascade (`GO:0070372`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `672017ffaba7c8bf769cb792a5e6b9f8fb6969c7a93d4cc0e670fd8082f975c3`；疾病通路关联 ID `a046b4934e291944afc88552bc501b4fde25e24f18d3f1ea536a9a396f2af097`。
- `TEK` → positive regulation of phosphate metabolic process (`GO:0045937`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `8b61b9c67249329b760e63c495c54e2e6974e2b7fd9ddbab0ad0b293f11e8087`；疾病通路关联 ID `50ef8cba9e20d70045137e4295d6d6e396726c51ac3626179b7c995818887d45`。
- `TEK` → negative regulation of vasculature development (`GO:1901343`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d93049b6cdea003889c42ea9f2471285cc55d1f9f436ffb999d9b706d14b7e71`；疾病通路关联 ID `724709f6cb596792000ed1e14b2ceb1a472a7962c99c412c0cbb474be1845f75`。
- `TEK` → regulation of endothelial cell migration (`GO:0010594`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d2ca18f731a4fe91fd30809d88d6f3595c84cceb8d37291be5844a111448835d`；疾病通路关联 ID `44b6f215656186368b386d7c2c0f0e740a25a47807f667e1b302c48e475df601`。
- `TEK` → positive regulation of cell-substrate junction organization (`GO:0150117`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ce891559d990cb7a7c2b5cd78480bd9837c43f6705abc0c38f7db213ff9a8a53`；疾病通路关联 ID `a753577a6eab89b3c82989df5c4c0521db63e28c7c08cf6ca3794ae089334559`。
- `TEK` → cell-substrate junction organization (`GO:0150115`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c8ce5de5d7755f6392eec33c1fc027d04bd3f5c3678aaddedc0fe9732902e899`；疾病通路关联 ID `a4dbe8075d8d617b6fbb17ae5fefecc1f5e5bba538303313e03ed1d606f503d6`。
- `TEK` → endothelial cell proliferation (`GO:0001935`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `86da1d82ba5c9892a498875870a29c892da99c2c56955104e98305c93280173e`；疾病通路关联 ID `8dc81fc4823f3f86f28e823b0345ee0c22007bd07b558722838ff07ddfd6c651`。
- `TEK` → regulation of cell-substrate junction organization (`GO:0150116`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `3e1ce7f0f34fde5a9121df26f66feed460f8d06626e383c22d3a7abc8ad83ed7`；疾病通路关联 ID `6dd9153bd4d99a7fdf6c75f7f4aa67bcbcb3055cf18331faf8dd8aaba61f6808`。
- `TEK` → epithelial cell proliferation (`GO:0050673`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `2b987ad8df00437d5d9f5dd8a40761c6fb4bdad0f1f85cf3d847f33130964f06`；疾病通路关联 ID `2b2df3c276167dd52de61de430ba76c64ad2ff635c0a1b927dea816368f76fc6`。
- `TEK` → regulation of cell-matrix adhesion (`GO:0001952`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `810a61d356916f69922fc0c08608ee91a97ea12800a08334ca5160924253a885`；疾病通路关联 ID `7346ab5af3782583af7b04152e70eb5c1073d5d9e27b7448d5f425633d2a601f`。
- `TEK` → regulation of cell-substrate junction assembly (`GO:0090109`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f99c14a0fb021dab8e56ce86968c5ab02489009f4148cf961b64d8e61f746c26`；疾病通路关联 ID `4cd4b043a30ce37ff93a422853c7e762ccff528269c9d9e096e8270f678ce132`。
- `TEK` → phosphatidylinositol 3-kinase/protein kinase B signal transduction (`GO:0043491`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a2e4e8a5e1ae2007e30f3bba2fc2b199cbb509e4fc0bcb0d2334d3c6a9e304c9`；疾病通路关联 ID `735797c1792b4ab370d5d54545ccedd587b270fd734695d47b6abfb7f5260084`。
- `TEK` → response to peptide hormone (`GO:0043434`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6731cfd303e481b0068cf594d375c6a68869ef26aea7b3b91615f936ccf569de`；疾病通路关联 ID `1dde14a49e5d2ed73349ad0c18ac29dbe5193ee580250cffacef76d66b2bdc63`。
- `TEK` → regulation of vasculature development (`GO:1901342`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `70b7c998bb9564c4a11d20cf1aed5e8513f2b30859dfdc4ef8568a567b955728`；疾病通路关联 ID `9822982fb9d290e1803fc82c30295bd6540ff3821fbb14ec3957f5a4530dfc2b`。
- `CYP3A5` → retinoid metabolic process (`GO:0001523`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `2a4c179f7fe666d39acca21daf2259f52c2b494405511c0f73c573344995fb25`；疾病通路关联 ID `864f392e2b965771e4cc1bcd55d6e32cbd02d846399230b661b99bcb88f22e31`。
- `CYP3A5` → diterpenoid metabolic process (`GO:0016101`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ee3039076dc7be05f174a322a24a58dc9d22f5f2ba4be0ee09fbecbf9b855b80`；疾病通路关联 ID `51cb69e2ac7a0d181e89cce4ad06694e299d80d925f199b7132ad6b56251221e`。
- `CYP3A5` → hormone metabolic process (`GO:0042445`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `dd3be466f8e848bbb4895c38f547b81af2665588329edc4ff091b8cceb32ac59`；疾病通路关联 ID `34d38f5996fceeffc6c1315763a391885bc1a0f3af9f50a1082976ceb5170303`。
- `CYP3A5` → terpenoid metabolic process (`GO:0006721`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f0a04e4a715b784e6bd38edd85b1d27c9c2f3ef51efe48564e2b07089aabed57`；疾病通路关联 ID `3b8a4822e157890e7efdd428597b64f77f1dabd1a2ab3d02b1982d6261824f19`。
- `CYP3A5` → retinol metabolic process (`GO:0042572`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `fc7b0d98361b3292fc0ac0458e3006619b1b00478a0ac557eff66d45b265c831`；疾病通路关联 ID `097ca85cc46fba6161fbb650c3f98fdadd24bd9f395867253879df8290cd716c`。
- `CYP3A5` → olefinic compound metabolic process (`GO:0120254`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `57f50b3cb08d15afb9c1fe17e7f8f92a61db6c6430666e8153ac6c9fd269ba0a`；疾病通路关联 ID `b5909ed0415033b6da40ae89a1563636b25fbb04a0c422a52f7ddfdc22f09d91`。
- `CYP3A5` → steroid metabolic process (`GO:0008202`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `199ac0f8aa26411e766a990954e5db8e794d33d8e54405656aec11aca092a673`；疾病通路关联 ID `e74007953196bcca19b4a729d34e3cfc5822eb3e93f7b93fd09bbe63b9fe3361`。
- `CYP3A5` → isoprenoid metabolic process (`GO:0006720`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `3eed6458e9a9e9ffa393699c71bd19aae262be9596f6835c1eff72927b866723`；疾病通路关联 ID `10f3eea3e304f06ca7768d18d041b36f15b9211c7680011cf4548bd0cd2bb9ee`。
- `CYP3A5` → primary alcohol metabolic process (`GO:0034308`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `8971f2fe35c4dbf6ce1b976fc50097d3070468036452f5ac51140b11872af07f`；疾病通路关联 ID `dd2a209c824e418eca020e28d9df0f1ed5e71a5b5d93fa20be6a3634c15c8b8c`。
- `CYP3A5` → alcohol metabolic process (`GO:0006066`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `515015fb3597c9058cfa97254aee4f0221a796f49c86039c15ade6e6fbb443f1`；疾病通路关联 ID `003edda7a3bc3fd756787a5be7aef5998249c4eeebfa590d2e3f27da708bcc48`。
- `CYP3A5` → lipid modification (`GO:0030258`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d0ba610ce1a72d95e6ea87c578080d4584c3ff0283959899bc83fe90974073f6`；疾病通路关联 ID `8276560e18197da9cbac3f90fd8b4f3b07c7437c79c7ad021344946402f152be`。
- `FGFR3` → HALLMARK_ESTROGEN_RESPONSE_LATE (`MSIGDB:HALLMARK_ESTROGEN_RESPONSE_LATE`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `73e8d71931cc54347c54375f3f20c19281250c9af40c60f4da1f040374015007`；疾病通路关联 ID `939a612fbaa6c4ff6dd502605580e5feaf48b775432c5243902037122b98d48f`。

当前 S1 富集摘要：肿瘤上调侧突出 DNA replication、E2F/G2M 与 estrogen-response Hallmark；肿瘤下调侧突出氧化代谢、呼吸链/oxidative phosphorylation、脂肪酸代谢等。富集与路径重叠仅为注释关联，不是通路因果证明。

## 独立验证、机制假设与冲突证据

- Exp010 独立队列同条件排名：125.0；外部 S1 条件级排序与主排序总体 Spearman=0.544，Top10 重合仅 1/10。
- PRISM ER+ 平均敏感性：1.0327045557973333，细胞系数=9.0；PRISM 相关性弱且没有显示 ER+ 选择性，不能作为 S2 药效确认。
- 候选机制摘要：图谱精确映射显示 ABL1、FGFR/KDR/KIT/SRC 等激酶靶点，其中 FGFR3、RET 在本 S1 上调，KDR、TEK、CYP3A5 在 S1 下调；这形成多靶点信号假设，但靶点方向不一，不能将整条路径解释为单向逆转。
- 文献链接：[https://www.accessdata.fda.gov/drugsatfda_docs/label/2020/203469s032lbl.pdf](https://www.accessdata.fda.gov/drugsatfda_docs/label/2020/203469s032lbl.pdf)。
- 本项目用确定性证据模板整理解释；未调用 LLM 生成本候选机制正文，因此不把模板内容标为 AI 输出。

## 局限

该药主条件仅由 1 条 LINCS signature 支持。WTCS 是表达逆关联，不等同药效。靶点关系与机制文献可能来自一般药理，不代表在 ER 阳性乳腺癌中直接成立。当前图谱没有可审计 PPI 边；不推断一层 PPI 扩展。后续需要多签名/剂量的重复、ER+ 模型剂量反应、正常细胞对照和机制实验。

## 可追溯文件

- S2 原始评分：`results/final_signature_scores.csv`（signature ID 可检索）；候选证据：`results/final_top10_evidence_matrix.csv`。
- 图谱关系路径：`mechanism/top10_mechanism_paths.csv`；原始图谱查询结果：`mechanism/final_neo4j_direct_targets.csv`、`mechanism/final_neo4j_s1_pathway_links.csv`。
- 逐条引用登记：`mechanism/top10_evidence_citations.csv`。
