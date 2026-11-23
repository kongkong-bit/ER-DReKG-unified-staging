# 4. doxorubicin EvidencePackage

## 候选与 S2 筛选依据

- LINCS perturbagen：`BRD-K92093830`；主条件：MCF7 / trt_cp / 10 μM / 24 h / distil_cc_q75≥0.2。
- WTCS=-0.467169；项目记号 reversal_score=0.467169；签名数=1；签名 ID：REP.A026_MCF7_24H:L19。
- 历史 B200 置换经验 P=0.0004997501249375312，BH FDR=0.0039334146486079，置换数=2000.0。该检验只覆盖 Exp008 历史 B200 分析集；NA 表示未在该历史文件测试，不能当成不显著。它不是临床疗效概率。
- Exp006 历史稳定性：A rank=5.0，B rank=3.0，稳定性等级=low；可用 24 h Q2 剂量数=6.0，跨剂量负 WTCS 比例=0.8333333333333334；限制=single signature。
- S1 规模敏感性同条件排名：A_original=39.0; B100=29.0; B150=11.0; B200=11.0; B300=3.0; B_matched125=39.0。全局结果显示 B100/B150/B200/B300 相对原始 A 的 Top10 重合分别为 8/10、7/10、4/10、3/10，故头部名单对 S1 规模敏感。

## 已知靶点和关系语义

精确 InChIKey 图谱映射：exact InChIKey；GraphBuild=`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e`。仅报告当前构建中存在的关系：

- NOS3 (`ENSG00000164867`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `71a826b87bdaf7aa95c251934e5623db2ea8a86e8666e47aee4cbd8c0b2b1912`。S1 direction=—; logFC=—; FDR=—。
- NDUFS2 (`ENSG00000158864`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `e4856c6760a1418bbd7127776dcef96880305c151f74d51237964a83250d0be6`。S1 direction=—; logFC=—; FDR=—。
- CBR3 (`ENSG00000159231`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `9d9762a5d03bd180d891bfec49834fbd4db75a9da731a44d5a8cf344fe7e4106`。S1 direction=—; logFC=—; FDR=—。
- CYP2B6 (`ENSG00000197408`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `99d99233aee268e716549ce9e4964f6637272019f77131152664a62e1983dc31`。S1 direction=—; logFC=—; FDR=—。
- NDUFS7 (`ENSG00000115286`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `80e72159fe781af66bebb5f7c2ca912ceb3cf216fb346d55b71f7b4cae747b30`。S1 direction=—; logFC=—; FDR=—。
- ABCC2 (`ENSG00000023839`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `b9423bf477d3758fe62bd524b7f3deee4ff561035e5b5e1c2390d6294f5b9f7f`。S1 direction=—; logFC=—; FDR=—。
- NOLC1 (`ENSG00000166197`): 关系语义 `TARGET`，来源 `DRUG_BANK`，Evidence ID `d7c42225a47d3987c1053c62a9efd375f520a19427471d1804afe8b0ab174207`。S1 direction=—; logFC=—; FDR=—。
- RALBP1 (`ENSG00000017797`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `9ddb39eb0bbc2a141d412d1ed3f0ef480ad380de991df5c7b353b0c982878f65`。S1 direction=DOWN; logFC=-0.362185609424063; FDR=0.0456006619394288。
- ABCB11 (`ENSG00000073734`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `8923537aa63326cfa7a50112d476d4b9784f9e596a064ad8ab6837e74818be08`。S1 direction=—; logFC=—; FDR=—。
- NDUFS3 (`ENSG00000213619`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `525307dc6f59555208bfad8a989a1e3a3a7c3bc2d57d64f24b9950085307d3cd`。S1 direction=—; logFC=—; FDR=—。
- AKR1A1 (`ENSG00000117448`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `465c69940730e1f0ffcbc10fc8eb38c6636535580af64bd4e2bb759e52b4e256`。S1 direction=—; logFC=—; FDR=—。
- CYP1B1 (`ENSG00000138061`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `85d5231e7b35e388c29ee5a69486c329437e8417106a9ca30b64a2a055d4310d`。S1 direction=—; logFC=—; FDR=—。
- CYP3A4 (`ENSG00000160868`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `a827ebfec180c1e604a8489cb6d86cb2645aec6e9924f2ee3ffc41f445d4921a`。S1 direction=—; logFC=—; FDR=—。
- NOS1 (`ENSG00000089250`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `ac16d0f0102fabcd86e92625d5487af15f971e7050204a30fd8047e116398277`。S1 direction=—; logFC=—; FDR=—。
- ABCC1 (`ENSG00000103222`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `e7afc919c3c345016fc1006cbaf359fc0fba8d9724ea47e4a2fbd5dfb2287a3d`。S1 direction=—; logFC=—; FDR=—。
- NOS2 (`ENSG00000007171`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `6413b0d1dee52d9434de9bfe4aaa1ef94dc9d63b6269868966accce268428694`。S1 direction=—; logFC=—; FDR=—。
- ABCC6 (`ENSG00000091262`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `9bb6849862f8f9db1faad49b26ea7069e3c14306c84c00a676d2beb4642aa7e0`。S1 direction=—; logFC=—; FDR=—。
- XDH (`ENSG00000158125`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `f739d1216d7185826095f0152245c89d3ea5d25ff52881e6749a9b856a5a63d6`。S1 direction=—; logFC=—; FDR=—。
- ABCG2 (`ENSG00000118777`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `40f07e2865c2a6ae24c43fb8e233201ae40ac9be2be36ef8bde8aa52685a5b20`。S1 direction=—; logFC=—; FDR=—。
- POR (`ENSG00000127948`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `688e5107fe81c66fc5e2a6d5700f390bb4125993a2aa933574f1dac293c30e32`。S1 direction=—; logFC=—; FDR=—。
- ALB (`ENSG00000163631`): 关系语义 `CARRIER`，来源 `DRUG_BANK`，Evidence ID `3febd2a6e2a89c74a459d109303f60f6138ae73440921fab17a7b9ef3ede25f2`。S1 direction=—; logFC=—; FDR=—。
- CYP2D6 (`ENSG00000100197`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `a1ceaa6093b6a2df8982e252e9ff5255cc8a8437d032585a05521aa0a8d87681`。S1 direction=—; logFC=—; FDR=—。
- ABCB1 (`ENSG00000085563`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `b2a7d7217123bdbf9a7ffba792c873d98dd373487c8c757afc6d09b6e96713eb`。S1 direction=—; logFC=—; FDR=—。
- CBR1 (`ENSG00000159228`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `9f9588c13e4fd3b29bf3972cd2b62947df35c6c93b6359800901a2422b10acd0`。S1 direction=DOWN; logFC=-0.511930094405622; FDR=0.0349474024219736。
- ABCC3 (`ENSG00000108846`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `48d71fcd936c3e74dda9c19d81431b3b1ee513aa86ed6694b90fdbad71b4745f`。S1 direction=UP; logFC=0.572919850064967; FDR=0.0454610728291714。
- NQO1 (`ENSG00000181019`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `311dba9d91bad3e337560b4dbb4a76ab496565939bd58458007df0da04b9efd0`。S1 direction=DOWN; logFC=-1.36032427323881; FDR=0.0166341746791992。
- ABCB8 (`ENSG00000197150`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `9d28f0d3b9dad4dd67b8b65eb4281fb7cba2749c1c083639970f71d2891515d4`。S1 direction=UP; logFC=0.213174702876205; FDR=0.013315363828234。
- TOP2A (`ENSG00000131747`): 关系语义 `TARGET, INHIBITOR`，来源 `DRUG_BANK; OPEN_TARGETS`，Evidence ID `5d997674034af750148403cb1ed2dc913d2b6f0494a2d893b0f755a65e480c89`。S1 direction=UP; logFC=3.22949300583669; FDR=2.53520344380651e-11。
- ABCC10 (`ENSG00000124574`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `91bbe08e4933b0f6bdd66f6a55f2f3379420623b3a525f61eeee66fff89a0a17`。S1 direction=UP; logFC=0.983047520388054; FDR=1.4038400990993e-06。
- AKR1C3 (`ENSG00000196139`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `cce3978a813f6b777d21ca589a2b4efe95db2c34411de6def1661f6e705a7319`。S1 direction=DOWN; logFC=-4.38397153274013; FDR=1.02275341457333e-10。
- SLC22A16 (`ENSG00000004809`): 关系语义 `TRANSPORTER`，来源 `DRUG_BANK`，Evidence ID `4f20c2804ae6d7737a1f965ba4891411703db2ebb6478f947ab43c0fdcb4d212`。S1 direction=DOWN; logFC=-0.227708378482443; FDR=0.00320497052334189。

## 靶点到疾病异常通路的证据路径

- `NOLC1` → HALLMARK_MYC_TARGETS_V1 (`MSIGDB:HALLMARK_MYC_TARGETS_V1`)，S1方向=—，GO/Reactome/Hallmark证据 ID `fb4aafbca8d7fc29263ebe0544d1c3f7d5112ca4a06a0a562ad046229828c119`；疾病通路关联 ID `b90192f02bd021b2cc978aaccc594e2aef64ac581e83b12e657c178530cc8300`。
- `NOLC1` → HALLMARK_MYC_TARGETS_V2 (`MSIGDB:HALLMARK_MYC_TARGETS_V2`)，S1方向=—，GO/Reactome/Hallmark证据 ID `fdc7b3d90968818c6f299cc0b447492e79a353fa38c13c50ed37537810711b7a`；疾病通路关联 ID `cd0007622e48322bf9419238c3e5cbf736ba6e47010f6da57a51d1ae01befbbd`。
- `RALBP1` → response to toxic substance (`GO:0009636`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ea1b4f9601066953fb5511c45a55619500d5efdb026a715dc66a41c5c13e8593`；疾病通路关联 ID `65b9bba83612481e59394200a2a68b2a5922edf6bcf6b60cf44a9b0d8099f275`。
- `RALBP1` → positive regulation of phosphorus metabolic process (`GO:0010562`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `7a6d793e1cdefcc8e8771e13a98fb5e0093371c84d7117bc4f4aa83109a18528`；疾病通路关联 ID `5432f1334ad6a8b5420a97403222337c97766ac08ee2e56057b6e9782fc0c732`。
- `RALBP1` → mitochondrial fission (`GO:0000266`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c05fcec266e20e08ec74e4d947e530ef5d59ceaef10234c5d191d0299ec41e00`；疾病通路关联 ID `c3021057f085ec4f670f9bf488f2f1705c4f91f74ff6eccc6d0d25b78c77a7b9`。
- `RALBP1` → taxis (`GO:0042330`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `235f8987229dc886e507752dca51cb5edb81cb7a702d9758c9f4d916d3bf8c11`；疾病通路关联 ID `0183c368ee2899fa14555eaaa0323cb70fae931922edb49b16d64a86180f0981`。
- `RALBP1` → detoxification (`GO:0098754`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `1feef62adec98757cc830922ad40e6d8864f425dc5e978b0be072f48d8bd1156`；疾病通路关联 ID `c7e2a9fda67a0421ea5f8211c68233bec1dc7b895674a9901d01b0647f61869b`。
- `RALBP1` → small GTPase-mediated signal transduction (`GO:0007264`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `87f5ab1240a3a8b54b741aa9672945eec021230a6dd9ef2d45aef83392bc15c0`；疾病通路关联 ID `e6a875d8415f60e03ecbc60fd57f7bbbe382a4abd1ecf1cb6c811b74afd36e24`。
- `RALBP1` → chemotaxis (`GO:0006935`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `18bdecbec5a0ae5243d8615a1e3da80478f04e00145abe3c96d07c389af6a3b8`；疾病通路关联 ID `4d3e55a8c19abea3e704f0b8242f32aafd49034d9e428e81f3f9292c46b14786`。
- `RALBP1` → mitochondrion organization (`GO:0007005`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0e247f84bf935630be246ddb0cffb52d3e9fca7be9d5e5baa39ae991f8570c2d`；疾病通路关联 ID `91f16f83f9f1362d0c382e6ddaa2900ca7ab7efb03e0e19349590019a0bf952b`。
- `RALBP1` → positive regulation of phosphate metabolic process (`GO:0045937`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `097620cfe81f57337eee82f43305ef26e0f0e8f74e4a2c0bf5d5bad6a6c2b328`；疾病通路关联 ID `50ef8cba9e20d70045137e4295d6d6e396726c51ac3626179b7c995818887d45`。
- `RALBP1` → Rho protein signal transduction (`GO:0007266`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `04d5c36055a4a2642e3e4dc06c7cef6b8700884466284df4138a6371c60eaad6`；疾病通路关联 ID `4f22b8c6e58f0fc7f137cc951a71ed197fa38dad52245b0106c5cfa9fe1f7224`。
- `NDUFS3` → HALLMARK_OXIDATIVE_PHOSPHORYLATION (`MSIGDB:HALLMARK_OXIDATIVE_PHOSPHORYLATION`)，S1方向=—，GO/Reactome/Hallmark证据 ID `19104dc3493bbbaaacda99b7189aa972bc8d013f43532420dc88cb1c44f487a1`；疾病通路关联 ID `a50cbf20eb8bab091d5b1b830fc14aa68546b766571584a7a1c4725621f27544`。
- `NDUFS3` → HALLMARK_ADIPOGENESIS (`MSIGDB:HALLMARK_ADIPOGENESIS`)，S1方向=—，GO/Reactome/Hallmark证据 ID `5afe5ab05b999113aeb92e77352a9ba5941e1304aac9aa35d1f6c2a643b88546`；疾病通路关联 ID `a2f092cb0e0e742c07755ed5fa0297e0140e5968540531bb7ba2cd940681e0cb`。
- `CBR1` → olefinic compound metabolic process (`GO:0120254`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `dabf8fffe660562da132550feffa9f528af371c8689d0e15d3e2041ab46e0ec7`；疾病通路关联 ID `b5909ed0415033b6da40ae89a1563636b25fbb04a0c422a52f7ddfdc22f09d91`。
- `CBR1` → steroid metabolic process (`GO:0008202`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c0a37b0b184be77589a450ef2adece606af6affb68ff597b142f25f1972685d7`；疾病通路关联 ID `e74007953196bcca19b4a729d34e3cfc5822eb3e93f7b93fd09bbe63b9fe3361`。
- `CBR1` → monocarboxylic acid biosynthetic process (`GO:0072330`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `8bdf177b156defdd117c07d380cdc7b0c5e711cb3345c2778a8a9c47dc0c290a`；疾病通路关联 ID `6f3dc152545b26857aaff3888b3d5c812b29c15be6901458e0daeea3fa79370c`。
- `CBR1` → prostaglandin metabolic process (`GO:0006693`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `4b85de22fee0dc35c8a5522cff4b5d711ddcd86af01851e09ca3a252343c5f53`；疾病通路关联 ID `42d9193ef56101f3f11d351ed3ee65f04e6cbd9b2dd53374fc508447cd053a80`。
- `CBR1` → prostanoid metabolic process (`GO:0006692`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0a87fd653b2393c206abde7a109016f3fc9ee01bcbfce521f00c630e7302f58b`；疾病通路关联 ID `cde12b27c163e284bdb027b43045db9b6e63d5b668a0b9b3f97d6d530a612ddc`。
- `CBR1` → fatty acid biosynthetic process (`GO:0006633`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `1d48ecf27cc7fb8626d9838ee2a1f9d2cca8f5b4830d36734c43a52b0b012d5f`；疾病通路关联 ID `c1a61507ade3e4673dea6e1b85f528d331e199a7d491c70746673511462dab52`。
- `CBR1` → organic acid biosynthetic process (`GO:0016053`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9bdfd295b83910306217f071b8ae738d7fe5c4d6ea145932de6fa7e46a5fcd62`；疾病通路关联 ID `162dcff9ce3f10b8f3f0685d33eed738ef86342c1d23dbaeb947664ac9211db2`。
- `CBR1` → fatty acid metabolic process (`GO:0006631`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `83e85cccba79982c16efd87c841b1e47e8e3bfb924aaf19d2ef2e818ecf37e72`；疾病通路关联 ID `fd71ef922c49921e7498b72e20cbc7fbed22798f8082c27bfe3c63e568a072ff`。
- `CBR1` → carboxylic acid biosynthetic process (`GO:0046394`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `903b8ef807c9bc3217a7ac66340d1c3865ef2e70b76118baf0a80301a73ec25e`；疾病通路关联 ID `c2611583f35c5c7371a19cf7863cc76faf5e46a9a63fab5c751390cc3b66f005`。
- `CBR1` → reactive oxygen species metabolic process (`GO:0072593`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5a1398f218625819e69cbe5798d716f562e3bb71d6350014be639f41aea39084`；疾病通路关联 ID `1509c16bf38164c94ad343d23d2376a63c51a33e604b49fa5487ee9404b31a9e`。
- `CBR1` → Fatty acid metabolism (`REACT:R-HSA-8978868`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `698fadaa14d282f2cf5ffb59f635ae541d933b204308aa547bdc2f9c2115fe7e`；疾病通路关联 ID `04cb248d6c8a79e75d78d451d0ea4ab78b9cbba0bfab8303f4872841e9d19450`。
- `CBR1` → cellular ketone metabolic process (`GO:0042180`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `dacf4229636fd0ca53229331ed2486ceb343fdda7fe0057a83f647a5f6261599`；疾病通路关联 ID `8bd7c249ab23302ceae2e3d18e3fcb6dbfb7f90b0e409bd0ae0927553cd41180`。
- `NQO1` → response to lipopolysaccharide (`GO:0032496`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6116aa5d0d9cf6d265ac34d05ccb65c0225db3b3ea68312308ea081045d4f6a7`；疾病通路关联 ID `20e549e0450c652f778a2498fe769d4a1b2379dfcd828ff806476631a23eb948`。
- `NQO1` → reactive nitrogen species metabolic process (`GO:2001057`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5a4ab8ba60044d7fec96358a8a8a90f9513d3ab69bfb2adc17e5d4a2f9716349`；疾病通路关联 ID `b692edb94933c393b9c15005a4d7fa9d3adcab83a7030b9f2ae90d00af14c7a8`。
- `NQO1` → cellular ketone metabolic process (`GO:0042180`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `1aad4044b7c5cab59333a2ecbc81f77e98d733fd57d094463ea9caf724edffd8`；疾病通路关联 ID `8bd7c249ab23302ceae2e3d18e3fcb6dbfb7f90b0e409bd0ae0927553cd41180`。
- `NQO1` → detoxification (`GO:0098754`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `1c55a99e3c0242e3fbb1ce83758fe9c9d126a035ec64fba7062799b9a4b18c73`；疾病通路关联 ID `c7e2a9fda67a0421ea5f8211c68233bec1dc7b895674a9901d01b0647f61869b`。
- `NQO1` → response to molecule of bacterial origin (`GO:0002237`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `263c201529b902e14a6024d036ac51be866e83f9424cfcfb9920918e352a9803`；疾病通路关联 ID `386b2250a238cf23489f0e03fffba4f33430f9b2eda5a43075f7b55c4be52db2`。
- `NQO1` → reactive oxygen species metabolic process (`GO:0072593`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `7fad3705643bd5db9bf17ac022725b22657bf73bb6a494994412e0b361eeec44`；疾病通路关联 ID `1509c16bf38164c94ad343d23d2376a63c51a33e604b49fa5487ee9404b31a9e`。
- `NQO1` → response to carbohydrate (`GO:0009743`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a24a33901ff0000c8a70ac1b8fbc6a6e859b0210c66bb635709fc9f49a52a533`；疾病通路关联 ID `3e073822f17bee2ffc5671ab66470b2745fcb2c1c6663505272e9004e1a275b6`。
- `NQO1` → Metabolism of amino acids and derivatives (`REACT:R-HSA-71291`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a028d62bc2923ce1b3583df0c2dbfd83b7afb6a13ca0755b6a1833cb078011a5`；疾病通路关联 ID `cc98c5fed03ea71e005eff8332d54e0cc2f00c7d706f7ceb2fdc416e19272ffa`。
- `NQO1` → HALLMARK_REACTIVE_OXYGEN_SPECIES_PATHWAY (`MSIGDB:HALLMARK_REACTIVE_OXYGEN_SPECIES_PATHWAY`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `dd470b51c7a4a5b4363db6723da1173a4ef7d7be56f228b0e1e2198e5d835a87`；疾病通路关联 ID `a68ef67e4fc3632d8da85d8650df486d5eb5439ef0cc5317aeb21225b68a9804`。
- `NQO1` → purine-containing compound metabolic process (`GO:0072521`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0bee1ae847b5a4b016bd34ea8502658c2eaec5273fc094b3dec1e3b55c615668`；疾病通路关联 ID `87732f65014b015a6a7e05fa7c8e5d684d1642825d138b24528614a270660dd1`。
- `NQO1` → nucleotide metabolic process (`GO:0009117`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `7f1b3970d5e631463039a1f00dffc5803701bc8c7860f8c48c76e3bf6fa360b2`；疾病通路关联 ID `2614375a1ee780a83b2133c287c7036e0860322fdcb9032f4fd402333a0193be`。
- `NQO1` → response to oxidative stress (`GO:0006979`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `8426a38db0580dcd69b70b47a406e6511fcfeb1a6e6024219c5d6fd0a89f697f`；疾病通路关联 ID `7bc55156b8806c9cf65a2209a4395024f834aa41a7f11093dcf423f6640f6845`。
- `NQO1` → response to nutrient levels (`GO:0031667`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `eb06164f4f988eb82c61c7b505a973573c8b4b2f84ab1aa04b4f7a40022dda00`；疾病通路关联 ID `405bb6061284d8bf5de468eb631870634d8e2fb9052656a541d71edf4d78a8ef`。
- `NQO1` → nitric oxide biosynthetic process (`GO:0006809`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `4717f90ce27401838fe82a6617e84d131df52c2e136db211becf5fd08e693e56`；疾病通路关联 ID `18fd9dee07bfdfa9c8bc73799d4dc6c99aaf7ee73ce171eda4d21f9fd6fd1583`。
- `NQO1` → response to toxic substance (`GO:0009636`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f46d0fe1e22339afe10f1a09e4e56e6f6b858aa43b959323ac390f5964336298`；疾病通路关联 ID `65b9bba83612481e59394200a2a68b2a5922edf6bcf6b60cf44a9b0d8099f275`。
- `NQO1` → nitric oxide metabolic process (`GO:0046209`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `156e2588558a5dcd72c5facf70d4f0684c886546782a5e88ddd67656fe5d7bce`；疾病通路关联 ID `f62ba709540879ca8b2da4057c2bf17c46aa0fa8dc5368243c035f3ee11677b7`。
- `NQO1` → purine nucleotide metabolic process (`GO:0006163`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c015730583c8aa00159ce81a1197ad849c3d55eca1b9ba4b8407a612087ccdeb`；疾病通路关联 ID `d063643803ca69a507ca6701a30bc21c37633a63f7b9be718048eb4256211afe`。
- `TOP2A` → HALLMARK_MITOTIC_SPINDLE (`MSIGDB:HALLMARK_MITOTIC_SPINDLE`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `190e872a7dbc68a0646a0fc4999cec9a768734c1ed8441475a5cf908be8f9682`；疾病通路关联 ID `9fd3536f843d75cbeaae0c79c28c060f3f3ba0dcc4cea05ae45eb72482903097`。
- `TOP2A` → SUMO E3 ligases SUMOylate target proteins (`REACT:R-HSA-3108232`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `4f5ce70fb2b03ff158bb24ceb717f6de15c57b9f70cd032f858e6b37301efa35`；疾病通路关联 ID `21ece173843704f662c2dde69996ebaf6c1b106d485852a804e9801eed6d8feb`。
- `TOP2A` → DNA geometric change (`GO:0032392`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `e20b0124965233add89740fc832391088e53c39762d1c4c888f314513fce5ed9`；疾病通路关联 ID `319d8432181e6b72a2af3ebe5ab1a68ee63742f8ff42ccf57df31f3873a41b90`。
- `TOP2A` → SUMOylation of DNA replication proteins (`REACT:R-HSA-4615885`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `2a7a911bc8a51dd26bb001eb82f09aa969759023176521cdc6da2876d4e3dcd3`；疾病通路关联 ID `1a8641b82b377d96f39318480c04bdc8d0959b586c75f8c87c9ac23661f25a6a`。
- `TOP2A` → DNA duplex unwinding (`GO:0032508`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `77e48ff8fe0d346120a64117e3e2945f1273cda85eeada82e763f37666585636`；疾病通路关联 ID `688aa65c5dae57b289a59ae289319bc867d196012aa2f0cc8167f76a78ba92e8`。
- `TOP2A` → sister chromatid segregation (`GO:0000819`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `7bd12a0ebf7bb332a68667369003a29410782f4eaf9267e114113c5234e97a26`；疾病通路关联 ID `cc7ea431298b5d96ae8ce8db43b55c385e4a77f6eec0dd44eb0fa1cf9cd8b596`。
- `TOP2A` → Cell Cycle, Mitotic (`REACT:R-HSA-69278`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `5e601fe02758c39c9a63c5c8d6a10e94948ed75330689ee78cfd62f59683502a`；疾病通路关联 ID `b9e3d9d250aabd88ba397199e5a68d34a56ee0f6410c038bf9c6f6488643b117`。
- `TOP2A` → chromosome condensation (`GO:0030261`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `4d02f4d2795adc3bfc399d12266e1619416c76326650e7276653d5044db484ca`；疾病通路关联 ID `7ac30b3aac585a93bfc618d6f06dcab2bf3bc39191758096d87cf7da464073a8`。
- `TOP2A` → organelle fission (`GO:0048285`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `3e4bb63ddf39519d90b51285cac57e65b81054c73fdb8a26992dff8c3b2812bb`；疾病通路关联 ID `cf2290546aa82266aa1a90259f1fa131160496c2fc1ce1887caad968aee5a9c8`。
- `TOP2A` → nuclear division (`GO:0000280`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `a1267889756da90d6630b6fadbf7e4c965235ee8519ee35239d75e5034359619`；疾病通路关联 ID `a9010b26e55adf987adbfcf9e4f771cf2198737509fa765e62a4689225ffa7e2`。
- `TOP2A` → DNA conformation change (`GO:0071103`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `f186cc6207c0fbfbd5077a8650a9e0a33c411777b937595162357874520b81df`；疾病通路关联 ID `6fc9b5b69f959e826ad9f9f12be23c17fabd47003c4a7cb6da61cdd79fe2ba56`。
- `TOP2A` → negative regulation of chromosome organization (`GO:2001251`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `6b5981451b5fbbeee2bccc4f8f934903022551be7b356430562283eabf336a7d`；疾病通路关联 ID `f15cc7c01ad6bef28fafc1bbc135d4074615c0c589333cb28611b8f4742bf18f`。
- `TOP2A` → chromosome segregation (`GO:0007059`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `4dce73959cb17cbf92f33838dba1817764a3de7b88c2b98a5ec80756c0a3b15e`；疾病通路关联 ID `f85b1a2c33610d336d2b0af144ff585ee66acdaabf3d92ef07d5acde78112c6c`。
- `TOP2A` → viral RNA genome replication (`GO:0039694`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `c3e5447f72e2e11f6a637cad00130026363804f5be5f3568e6e89eeb8e9d1d92`；疾病通路关联 ID `076fe3ab1080a1aca3e456121c22c41a3ef4b1a1e1912da9320d7a3ee51bcba7`。
- `TOP2A` → nuclear chromosome segregation (`GO:0098813`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `482ee6ddd123b458a7c24e34327012fda24c888a88c30fcca814967e9c90c3b3`；疾病通路关联 ID `8b87ffdcdbea16450222a8646cc7b3ceab899177948010adcbef0857016c964f`。
- `TOP2A` → regulation of chromosome organization (`GO:0033044`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `81b96a9e6fbc44c19f2eca3daa95ea1a3e429bd80db3442045ef99390768d588`；疾病通路关联 ID `3084b0ae2344662260fc2e35cfc78a12067c5cad3cae051314bf792647855180`。
- `TOP2A` → viral process (`GO:0016032`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `20c80c123f55e8f2f2c8bceeaf7ac23e934278960c40bb478abdd007dad2bd93`；疾病通路关联 ID `5276adb6c99a8a3c62c203bc44c701fff56818b21cb46d60eddfb66f0f855f96`。
- `TOP2A` → SUMOylation (`REACT:R-HSA-2990846`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `fb78d02f59223f5fca8bb67605f55721f869dd8f185cdfdc15b178ba8938b022`；疾病通路关联 ID `e14ca93b77ffb37756ae7341ca632a510a5be19c7f07ea80ffcae51b763b725f`。
- `TOP2A` → DNA recombination (`GO:0006310`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `851395906df9df894e0de141c307a382c256e02b35837c6232470df7411ed738`；疾病通路关联 ID `2aeb3db619bb95ddf4b5f8b5a42e94115c4b6be3b01d82ca4548477c9535b97f`。
- `TOP2A` → meiotic cell cycle (`GO:0051321`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `1f062c5ccc87e598a750c0536877a1ac4fb86af5350759f2c9ca35101b3aa594`；疾病通路关联 ID `02fa83b91db6c4342483607eef314cdfd896da3194725cfea640e02b8ec52e34`。
- `TOP2A` → meiotic cell cycle process (`GO:1903046`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `b423db750d2d7bc95bfa35e731297fe3af649d0f442a0932c32faee0a3eacf91`；疾病通路关联 ID `7d97e69e4649ff0b11c0bfd1d8088797bcbb51b466a3b4c43e48f0fc20dc05e4`。
- `TOP2A` → HALLMARK_E2F_TARGETS (`MSIGDB:HALLMARK_E2F_TARGETS`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `5fae77bea5c64635e03129a19553b133f8f69e94ca4d055bf6627f79eb9a8be6`；疾病通路关联 ID `b7e2a83d6b4833d9c436039ccdbd147f34eabf808d75c5fd013c9433b3ca1693`。
- `TOP2A` → HALLMARK_G2M_CHECKPOINT (`MSIGDB:HALLMARK_G2M_CHECKPOINT`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `ba7fe0b5abb62be1ac3eba3a3c28f39eaf91a0f1d951f98a1e48004b591ea32a`；疾病通路关联 ID `9e1cb8234373f4d97636a0b3870e4dcbf4fae01f68caf3fd502b15e7169b8914`。
- `TOP2A` → HALLMARK_ESTROGEN_RESPONSE_LATE (`MSIGDB:HALLMARK_ESTROGEN_RESPONSE_LATE`)，S1方向=UP，GO/Reactome/Hallmark证据 ID `f24440c7f8b39e0d8d83bfb8e8319b0275ea9ff40a86000da75e7afc02b6eb20`；疾病通路关联 ID `939a612fbaa6c4ff6dd502605580e5feaf48b775432c5243902037122b98d48f`。
- `AKR1C3` → prostanoid metabolic process (`GO:0006692`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d8fe139264dba679e4fbf44ace484133f810b34988ccd567eb6e5299a8c32e78`；疾病通路关联 ID `cde12b27c163e284bdb027b43045db9b6e63d5b668a0b9b3f97d6d530a612ddc`。
- `AKR1C3` → fatty acid biosynthetic process (`GO:0006633`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c3ebf6e54ee7cb0a8444449d15463db9cac98689ef78b795aee94b18644863ec`；疾病通路关联 ID `c1a61507ade3e4673dea6e1b85f528d331e199a7d491c70746673511462dab52`。
- `AKR1C3` → monocarboxylic acid biosynthetic process (`GO:0072330`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `88cfcbc45ff5acb1abbaa7e0e144552d08e062818b656c3137c787f6aa09ff89`；疾病通路关联 ID `6f3dc152545b26857aaff3888b3d5c812b29c15be6901458e0daeea3fa79370c`。
- `AKR1C3` → Signaling by Retinoic Acid (`REACT:R-HSA-5362517`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9fdbbd636439a8642bf65f58052f3906751b8fadf0b0cca250422d4c3e8732f5`；疾病通路关联 ID `f706a2f955d1812cd50368876d841efd6cfb66134575e64065d299c9d420ac3d`。
- `AKR1C3` → lipid catabolic process (`GO:0016042`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `14fd8ed31e633acc015d73cbea4c67aa3130a5bd9281ed79af3a65e349622093`；疾病通路关联 ID `df09d13c6ab56d3efd6dc69b02195ea999cc8d50afa11a140c404e5ee4babc16`。
- `AKR1C3` → prostaglandin metabolic process (`GO:0006693`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d58dc637273d33d2a82ac93352ba5edcba194d0492167320ffc21467cb0c0981`；疾病通路关联 ID `42d9193ef56101f3f11d351ed3ee65f04e6cbd9b2dd53374fc508447cd053a80`。
- `AKR1C3` → reactive oxygen species metabolic process (`GO:0072593`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `631f93342989d0cd2c6e8e4b9797d8bced6d3bf71b78a6e357bcbdbf6068593d`；疾病通路关联 ID `1509c16bf38164c94ad343d23d2376a63c51a33e604b49fa5487ee9404b31a9e`。
- `AKR1C3` → cellular ketone metabolic process (`GO:0042180`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e417bd6d5781212954cad435288bf2fc85f7193ee01714612ec44de84236506c`；疾病通路关联 ID `8bd7c249ab23302ceae2e3d18e3fcb6dbfb7f90b0e409bd0ae0927553cd41180`。
- `AKR1C3` → response to nutrient levels (`GO:0031667`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `32d2b42ccb409c0b782766bff3aaef6e5d748e57dd88b1b8f70f3c0f213b4329`；疾病通路关联 ID `405bb6061284d8bf5de468eb631870634d8e2fb9052656a541d71edf4d78a8ef`。
- `AKR1C3` → regulation of lipid biosynthetic process (`GO:0046890`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `189d1e4b9aa3e8cb5df9f53192e610d548060a2175b9dbeefc128191bbb9b573`；疾病通路关联 ID `de293a373eb72ab7ee0eb86f929aab5c8eae8a7b233c285787f86de3c2cfe201`。
- `AKR1C3` → retinol metabolic process (`GO:0042572`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d6d9b77ee1778466ce9d5046dc9757cbb3b37c554ca826ebe910cd63b9c88d49`；疾病通路关联 ID `097ca85cc46fba6161fbb650c3f98fdadd24bd9f395867253879df8290cd716c`。
- `AKR1C3` → primary alcohol metabolic process (`GO:0034308`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `872cdc1c2951788c2c205386683adbd93698ce5319cd90b8ac6b42d006bffc7c`；疾病通路关联 ID `dd2a209c824e418eca020e28d9df0f1ed5e71a5b5d93fa20be6a3634c15c8b8c`。
- `AKR1C3` → regulation of phosphatidylinositol 3-kinase/protein kinase B signal transduction (`GO:0051896`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `75958ddec39abcb1790b7d94ffbea5a35dab9fa6aa1a4f9d45d461e0c537a8ce`；疾病通路关联 ID `c8dda60f68509c6827132708d86743b70fb9d52f5a2208406eb049cef50c91d6`。
- `AKR1C3` → terpenoid metabolic process (`GO:0006721`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5aff83bc1624b7379dfb33e4e587d0c8bebfb5529839ee755682d176c3113957`；疾病通路关联 ID `3b8a4822e157890e7efdd428597b64f77f1dabd1a2ab3d02b1982d6261824f19`。
- `AKR1C3` → olefinic compound metabolic process (`GO:0120254`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a7859725f5eb9de76bfe6d8f66921472126bc35e90e92117b8334b3434984c37`；疾病通路关联 ID `b5909ed0415033b6da40ae89a1563636b25fbb04a0c422a52f7ddfdc22f09d91`。
- `AKR1C3` → cellular aldehyde metabolic process (`GO:0006081`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `98fa8aaafdcca2443c45169982ec24273d53f446eacb0f7818881ed127965e1d`；疾病通路关联 ID `599c0a009e335ab03333179e2d6de3cf4b393b08226990f1d15fd1fd0376f53e`。
- `AKR1C3` → regulation of lipid metabolic process (`GO:0019216`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `18bb7eca419e4471533d4666eafd25c0e9ee57826ad7babd01e2c203ada30f14`；疾病通路关联 ID `5f2f904f79ca6516e736d0ce6e4cfd17ee59635339a423c537191e4c8a2490c8`。
- `AKR1C3` → carboxylic acid biosynthetic process (`GO:0046394`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9efa366e4cf3a1a2b739d6321823115a8763e0fce08cb9863d71a36cd134c807`；疾病通路关联 ID `c2611583f35c5c7371a19cf7863cc76faf5e46a9a63fab5c751390cc3b66f005`。
- `AKR1C3` → alcohol metabolic process (`GO:0006066`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c4bdd5955b392b2265303f92cd497850e28752ee760b713cb1e7df6873d54f69`；疾病通路关联 ID `003edda7a3bc3fd756787a5be7aef5998249c4eeebfa590d2e3f27da708bcc48`。
- `AKR1C3` → phosphatidylinositol 3-kinase/protein kinase B signal transduction (`GO:0043491`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `937a79cf2443e2635031e6138919da318fa8a25c667641809b86fcfc2ac28c2a`；疾病通路关联 ID `735797c1792b4ab370d5d54545ccedd587b270fd734695d47b6abfb7f5260084`。
- `AKR1C3` → retinoid metabolic process (`GO:0001523`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c3cf10029fee885d7636a9f7c29b5a323b99910b8a25b2f567acd22b948282c2`；疾病通路关联 ID `864f392e2b965771e4cc1bcd55d6e32cbd02d846399230b661b99bcb88f22e31`。
- `AKR1C3` → positive regulation of phosphatidylinositol 3-kinase/protein kinase B signal transduction (`GO:0051897`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9037f31907612a8c1f3fd780f29af089458450df19295f58615abccf4f1647fb`；疾病通路关联 ID `74fa5d3671ef01b7b0d3faf369a47905a580e0f60aa2cfe0167c209aa84f8fa5`。
- `AKR1C3` → cellular lipid catabolic process (`GO:0044242`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `49bb2575a2914114831d4becc96164f39d0570e886b18bc0395396a813e35c28`；疾病通路关联 ID `e3bc50c5eec6ad5ee50b3a8aac09ccb0b1e542dc9dd3d65920aae12aaba1dfbf`。
- `AKR1C3` → isoprenoid metabolic process (`GO:0006720`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `97237258c36e90bbf8c41cdbf55ea177b6bed9e56324a70971a286917f2c7db0`；疾病通路关联 ID `10f3eea3e304f06ca7768d18d041b36f15b9211c7680011cf4548bd0cd2bb9ee`。
- `AKR1C3` → organic acid biosynthetic process (`GO:0016053`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5af16b5c74620a281384fe6e388bb7a048447b353794114571c07f88e4bd7e3e`；疾病通路关联 ID `162dcff9ce3f10b8f3f0685d33eed738ef86342c1d23dbaeb947664ac9211db2`。
- `AKR1C3` → diterpenoid metabolic process (`GO:0016101`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `b4e6aaec4ce075743ec36743c84f4ab17cf414e9298bc171bd7395cf70377522`；疾病通路关联 ID `51cb69e2ac7a0d181e89cce4ad06694e299d80d925f199b7132ad6b56251221e`。
- `AKR1C3` → C21-steroid hormone metabolic process (`GO:0008207`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `cfc62b2bd5cb9515193c42452023a175a7f6e2323365a917e5aa4a85e7063587`；疾病通路关联 ID `4cafbdd0fd7c0e7b0554aa7d230bd904085b6b5804ad27248b1ac13230b74991`。
- `AKR1C3` → Fatty acid metabolism (`REACT:R-HSA-8978868`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `3ede04f1ca6b82df165f4494addce2b673da5ad80d899a4c563fbcfc83224ab9`；疾病通路关联 ID `04cb248d6c8a79e75d78d451d0ea4ab78b9cbba0bfab8303f4872841e9d19450`。
- `AKR1C3` → cellular response to nutrient levels (`GO:0031669`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `4dbe00def683f9d61b5a0f8e5565b321122f9e6a696899cbd8defa728bf78547`；疾病通路关联 ID `24abf24b35b69c6a1e6c4d26693dfd67a3fd7a80f3023ec8768fa2284186a98c`。
- `AKR1C3` → small molecule catabolic process (`GO:0044282`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0540ed98f451f3461428b2be593f33902522f59c0bdbf57ba24a36c22ae597c2`；疾病通路关联 ID `60b5211b040d83481eade830a2c6256226d12a4fc4afe11dfad97a82de4eb2ab`。
- `AKR1C3` → Metabolism of vitamins and cofactors (`REACT:R-HSA-196854`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f4c89bde43187baea0f5178397646027084f1c9b74dac4ff38336de4f02c94de`；疾病通路关联 ID `11a70d54eb4b29f116aebda7dfac9827f25cbb170500e2f501d0649c7d9e1934`。
- `AKR1C3` → steroid metabolic process (`GO:0008202`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `3ea3c08ca84693655bbea4c8301e497f63071ba879be5f64d09ff52b5f7f215b`；疾病通路关联 ID `e74007953196bcca19b4a729d34e3cfc5822eb3e93f7b93fd09bbe63b9fe3361`。
- `AKR1C3` → cellular response to ketone (`GO:1901655`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `98bae327078aa5699c5a3fed0d459bc8be4ac0950a16d0d9be5bd19e46ccd549`；疾病通路关联 ID `0881dafd4dd6d36c856646de15d4f04cfb64c71fe77007a975b40fd117fe2c67`。
- `AKR1C3` → hormone metabolic process (`GO:0042445`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `22bf63a6a10513a532017587a2f9a375a69caeffe15d9afb59d66be3ac922024`；疾病通路关联 ID `34d38f5996fceeffc6c1315763a391885bc1a0f3af9f50a1082976ceb5170303`。
- `AKR1C3` → regulation of cellular ketone metabolic process (`GO:0010565`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d5ee8bc9c854b1fd9af9977b28203295e014f0ba15b5cbdac2f0f51779c06de0`；疾病通路关联 ID `0517e8c59a1b2f163d20c3c5f5815617247326d1d898d6ac1fa05005bb05a283`。
- `AKR1C3` → fatty acid metabolic process (`GO:0006631`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e4fdb857f71c3a92e65ce4f0fe1e4f31dc6023463eaecc723e213ccfaff665db`；疾病通路关联 ID `fd71ef922c49921e7498b72e20cbc7fbed22798f8082c27bfe3c63e568a072ff`。
- `AKR1C3` → regulation of small molecule metabolic process (`GO:0062012`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9b403f1518f98d4e07c1742ce09c5f4b495e07cbffae1fe7dfbe205c346493ca`；疾病通路关联 ID `d2cdd4d6838e0c8fa0b1b872dc82d577dbcfb39ca3dad423709246487dcb9924`。
- `AKR1C3` → HALLMARK_XENOBIOTIC_METABOLISM (`MSIGDB:HALLMARK_XENOBIOTIC_METABOLISM`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ee950f2dd3b60de0cfacb7ba060bfe6869629e38c8f93695302b61f3a0a6fc9b`；疾病通路关联 ID `836d255f36d123b7028b859f014b783b6e5f3d43b08f24070747920c6f3c7d35`。

当前 S1 富集摘要：肿瘤上调侧突出 DNA replication、E2F/G2M 与 estrogen-response Hallmark；肿瘤下调侧突出氧化代谢、呼吸链/oxidative phosphorylation、脂肪酸代谢等。富集与路径重叠仅为注释关联，不是通路因果证明。

## 独立验证、机制假设与冲突证据

- Exp010 独立队列同条件排名：352.0；外部 S1 条件级排序与主排序总体 Spearman=0.544，Top10 重合仅 1/10。
- PRISM ER+ 平均敏感性：3.1106043918433333，细胞系数=9.0；PRISM 相关性弱且没有显示 ER+ 选择性，不能作为 S2 药效确认。
- 候选机制摘要：图谱记录 TOP2A 等关系，并连接 DNA 复制、细胞周期路径；TOP2A 在 S1 上调。广谱细胞毒性和 DNA 损伤作用不能解释为 ER+ 特异或通过逆转 S1 起效。
- 文献链接：[https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/050629Orig1s033Correctedlbl.pdf](https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/050629Orig1s033Correctedlbl.pdf)。
- 本项目用确定性证据模板整理解释；未调用 LLM 生成本候选机制正文，因此不把模板内容标为 AI 输出。

## 局限

该药主条件仅由 1 条 LINCS signature 支持。WTCS 是表达逆关联，不等同药效。靶点关系与机制文献可能来自一般药理，不代表在 ER 阳性乳腺癌中直接成立。当前图谱没有可审计 PPI 边；不推断一层 PPI 扩展。后续需要多签名/剂量的重复、ER+ 模型剂量反应、正常细胞对照和机制实验。

## 可追溯文件

- S2 原始评分：`results/final_signature_scores.csv`（signature ID 可检索）；候选证据：`results/final_top10_evidence_matrix.csv`。
- 图谱关系路径：`mechanism/top10_mechanism_paths.csv`；原始图谱查询结果：`mechanism/final_neo4j_direct_targets.csv`、`mechanism/final_neo4j_s1_pathway_links.csv`。
- 逐条引用登记：`mechanism/top10_evidence_citations.csv`。
