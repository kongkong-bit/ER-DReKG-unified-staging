# 8. balaglitazone EvidencePackage

## 候选与 S2 筛选依据

- LINCS perturbagen：`BRD-A00147595`；主条件：MCF7 / trt_cp / 10 μM / 24 h / distil_cc_q75≥0.2。
- WTCS=-0.452738；项目记号 reversal_score=0.452738；签名数=1；签名 ID：REP.A012_MCF7_24H:B07。
- 历史 B200 置换经验 P=0.0004997501249375312，BH FDR=0.0039334146486079，置换数=2000.0。该检验只覆盖 Exp008 历史 B200 分析集；NA 表示未在该历史文件测试，不能当成不显著。它不是临床疗效概率。
- Exp006 历史稳定性：A rank=3.0，B rank=5.0，稳定性等级=low；可用 24 h Q2 剂量数=3.0，跨剂量负 WTCS 比例=0.3333333333333333；限制=single signature。
- S1 规模敏感性同条件排名：A_original=20.0; B100=18.0; B150=19.0; B200=17.0; B300=71.0; B_matched125=20.0。全局结果显示 B100/B150/B200/B300 相对原始 A 的 Top10 重合分别为 8/10、7/10、4/10、3/10，故头部名单对 S1 规模敏感。

## 已知靶点和关系语义

精确 InChIKey 图谱映射：exact InChIKey；GraphBuild=`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e`。仅报告当前构建中存在的关系：

- CYP3A4 (`ENSG00000160868`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `829f55ab30c0f2410ede541472e99ae8b5807b52c51725996e0d91128c709d59`。S1 direction=—; logFC=—; FDR=—。
- CYP2C8 (`ENSG00000138115`): 关系语义 `ENZYME`，来源 `DRUG_BANK`，Evidence ID `71209243e297d323fb3ce417629b53ceee656c8cdbbb03f79fcc420e6310248a`。S1 direction=—; logFC=—; FDR=—。
- PPARG (`ENSG00000132170`): 关系语义 `PARTIAL_AGONIST`，来源 `OPEN_TARGETS`，Evidence ID `fba4167f822b4d3a96da791edea42fdeae960c2cf5e85eb5a6c1f31018fbe6ff`。S1 direction=DOWN; logFC=-4.84089870604829; FDR=4.71136367105938e-21。

## 靶点到疾病异常通路的证据路径

- `PPARG` → sequestering of triglyceride (`GO:0030730`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6888f4c79fc18a64b52ca03e5cb77140ee84e040871c12d3a8d39d6fc24aae15`；疾病通路关联 ID `414d5585466a03c9b1391f8f747db236fddba6af1159d134084482a21437e31a`。
- `PPARG` → regulation of macrophage derived foam cell differentiation (`GO:0010743`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9592ae916cc5285c5e5d0c46b1810c827c5909c0bd862887366774bfd9d383de`；疾病通路关联 ID `a03642392060dbcb4226f964c30b4430d0fc54b62204791301cf2df33d1f20b1`。
- `PPARG` → negative regulation of smooth muscle cell proliferation (`GO:0048662`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5bfbfef09bf1fa67e52a626521a5efc4058bda8695742d4a30c616d70ca9a4f3`；疾病通路关联 ID `62a1531aad0894541d22680f74639bb5f532435882769e704613f4ec82f09c37`。
- `PPARG` → regulation of cellular ketone metabolic process (`GO:0010565`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `7d421e7b2fbcf9091e80c922d415c8f15750f1227f1fd8b4ad32d3c28bdce191`；疾病通路关联 ID `0517e8c59a1b2f163d20c3c5f5815617247326d1d898d6ac1fa05005bb05a283`。
- `PPARG` → cellular response to insulin stimulus (`GO:0032869`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5ce5fa9c7618c46316c0152e84a3bb81c2a9d3c6ced94434652252f22039d802`；疾病通路关联 ID `1f8839722bfe5bf3d625a9e8e1045d7436166e376fc0fbea2ba7db4fa9e13452`。
- `PPARG` → smooth muscle cell proliferation (`GO:0048659`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `8492b114660dccabf2de2d9de0c99c0f6f202761a7c78300f137aa4d2910c91b`；疾病通路关联 ID `b67a10a1436b1a8a7db001bcb703f342f0de68011488efb8a5d3d6c0e804bf0e`。
- `PPARG` → cellular response to peptide hormone stimulus (`GO:0071375`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `cd4e64dcab15eac67e34189e2213e1eee94541668ba4c8fdad560cc2ca055565`；疾病通路关联 ID `e32459e7fee49ab04b025d732c28ab508242499160050ea92c45af5f4f17fefb`。
- `PPARG` → endothelial cell proliferation (`GO:0001935`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c4b101463a62e9a8ad3d257d67039c2787bcc69ae495e69b703a9f7e5f6db811`；疾病通路关联 ID `8dc81fc4823f3f86f28e823b0345ee0c22007bd07b558722838ff07ddfd6c651`。
- `PPARG` → regulation of vasculature development (`GO:1901342`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f1302f1c179da9e414e9ea3026f7bceb3d636c44d157052a83cfa6c2b4d944ca`；疾病通路关联 ID `9822982fb9d290e1803fc82c30295bd6540ff3821fbb14ec3957f5a4530dfc2b`。
- `PPARG` → regulation of lipid storage (`GO:0010883`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `284fe739528e802c4d482af393facf1bac87b9e7e1291f91024a7a788a784ca4`；疾病通路关联 ID `99d0aa505a633c2259700cefd743c5f3e84e818985a46c539e12e83f58f442a1`。
- `PPARG` → positive regulation of lipid localization (`GO:1905954`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `622e4b9f19b06c247ecba64bbefcb01b5b04f4463a78f9e69eda912ec1b9cae0`；疾病通路关联 ID `64341b2736b67ed1eb888c6d7100fb290702175b25b54102bfb866e1c2e73b6a`。
- `PPARG` → regulation of lipid localization (`GO:1905952`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `af6a15baf381c7dc91ed888fe8cc6cec269e876ec043fa21e8757c8c3d12b5a6`；疾病通路关联 ID `08506981c536e6e7211251477b2e9ab6213958173fa8f1742c43659d0ea76dff`。
- `PPARG` → positive regulation of lipid transport (`GO:0032370`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `94b7471f1171437047160f68867c595c1d6c060cd84d3c5248158ff6a9e7230b`；疾病通路关联 ID `ddd53021d1d893d697cb5cf7c6629cd739b960f8d5ac4879570f891e11aa855f`。
- `PPARG` → regulation of small molecule metabolic process (`GO:0062012`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `454fc8278bd1f16e26cff8a528e3898f4d876600c1d59dc4b3ca446bb6019a9e`；疾病通路关联 ID `d2cdd4d6838e0c8fa0b1b872dc82d577dbcfb39ca3dad423709246487dcb9924`。
- `PPARG` → response to transforming growth factor beta (`GO:0071559`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `b95b0d56c73f511db284312fcbf164683058f12d38e742e7cfe1dec069c6e47f`；疾病通路关联 ID `d7913addcdd12a3b1f27aee841844d0e615e6b57af00fca768ff64a67a3ad1a0`。
- `PPARG` → negative regulation of endothelial cell migration (`GO:0010596`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6692fc770d9ebfd42568937419c9a388d798ca867914a26270801305c0b563d1`；疾病通路关联 ID `0549b047ad60469baefe95de479ef6a2a9ab5710886ae7d68c1b4ef36c035410`。
- `PPARG` → positive regulation of sterol transport (`GO:0032373`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `8ef120402aa4799300649fa112254348bc12bb11a7cb4b241534e063c27d1a36`；疾病通路关联 ID `ee7acebae09c48bd0dfa4a9f372f92e4d9c7e6d7bb5dbe11ca9a05a63be6f6a2`。
- `PPARG` → regulation of lipid metabolic process (`GO:0019216`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `658aca20b6255da22cac036b32a1c0ef428add81ed0c8696418eec0bf7f4abbc`；疾病通路关联 ID `5f2f904f79ca6516e736d0ce6e4cfd17ee59635339a423c537191e4c8a2490c8`。
- `PPARG` → positive regulation of cholesterol transport (`GO:0032376`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `de591c67452cc0a0759788f68b97ebc01b2717a835cc732154f1bc1e40a495d7`；疾病通路关联 ID `a79499a68bb554a7cd84645cf3e0a0219b563e29d5d1d8df185228bd9d48cd08`。
- `PPARG` → fat cell differentiation (`GO:0045444`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5c07b68cb4bf5383908eaffba6290a4602da13796e11fd80ef9d1c167cddb9dc`；疾病通路关联 ID `6daec45f2be1d8e675c081ab9571cdd32219bdfe084251dafef16f7ea8902e89`。
- `PPARG` → regulation of blood pressure (`GO:0008217`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `07e3369086b76552da838992c14ef7c7f9cdb1f11a32cb6fa08f6081fedfebb3`；疾病通路关联 ID `7a4ccd4e2a75d9bbe4f0c4df7fd66e8d77acfa8f709ead1a4c62839660939733`。
- `PPARG` → cholesterol efflux (`GO:0033344`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6be5feb64f5f19038436618c20db440abf0f2d13a5c2b972d22d928345a55936`；疾病通路关联 ID `11ec63d293197228c131b86b21b43f7c21a9744873f3cfc8440b7b7dec73bd4c`。
- `PPARG` → negative regulation of cell migration (`GO:0030336`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `20cf9334392f3318acb54588b6f8a0e05e06e95e9c03c550ad005324468fa251`；疾病通路关联 ID `71db82c1f315987368836f00b43ad1572e5be42fd74c0422b1eafdbe5d947c37`。
- `PPARG` → adipose tissue development (`GO:0060612`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `964639b475c74e2630de27e6b7297d4042f6ba0f327b9652328b87bc1ae3c41e`；疾病通路关联 ID `9a2ff6c8062cdbccacf8a306e05c010688e8ba8e4f42f0b4c0535a921d247259`。
- `PPARG` → ossification (`GO:0001503`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a458e886e0ccc8b8f2777561a9faf96a4cfe1e3691d33faf1b37744cc352e72f`；疾病通路关联 ID `808aa65462f43e4d91520ce6a337ba106e9180d2bb8fa1057377de329d82cd96`。
- `PPARG` → macrophage derived foam cell differentiation (`GO:0010742`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `846b6bde18c4bbdd00042c8438cccdb43c2e1c88efdcd216fef0566f46209fcf`；疾病通路关联 ID `e5aab487f9a507e9b73cf1d3fe20210d248ea5c061a7eb9b45708e0c789b675d`。
- `PPARG` → endothelial cell migration (`GO:0043542`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `51390e92cd8d0d14d4e2349eecf015e483860925bb2aeb7095a1c6c039cb6cf5`；疾病通路关联 ID `2ee8a37378e48094801869aefeb77dac866b40b9e651f16e2005473c5205dc00`。
- `PPARG` → regulation of fatty acid metabolic process (`GO:0019217`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e9e1a946b265d52a9150010b6490b83e011286aae1a7ad20f98cfedb117466eb`；疾病通路关联 ID `d540218d47b1b8d87cf220f47cd1f6cf83348d0126e8ac2c148e12d09257fe9d`。
- `PPARG` → positive regulation of small molecule metabolic process (`GO:0062013`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `aad4b9a319a7e8c6d7f72942960606c35242e19c1d8f39f0d6a98eaf9ab10f93`；疾病通路关联 ID `6023f81d4178de8487d5b59f67e50665f7b80341cc95abed5be0d2895d05936e`。
- `PPARG` → cellular response to BMP stimulus (`GO:0071773`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `3df0fece7863ba3e65ff8d2bdf67bce7537eb60a388a330325400a15ae401074`；疾病通路关联 ID `4509284f564dc5bed95017f62220dfb752bd29c18e5da4452cf5f2eee1abf049`。
- `PPARG` → myeloid cell differentiation (`GO:0030099`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `fe5fc016736e3384c338704320db1ec4d96d08d299f7053bb4f91b5ecb2f322e`；疾病通路关联 ID `750e32870e8989ea757b4ebc5c1b573a7f39e623da0e7b14e1297a2cc7c4559d`。
- `PPARG` → regulation of osteoblast differentiation (`GO:0045667`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `b45572c229fbc5d883e74ed38bf286021cbd2d9cdcd8b920f903b6e7230f8ac8`；疾病通路关联 ID `475a135e0af58f1af05a675473437ae88c23957f2c537c524375b20ad819840d`。
- `PPARG` → regulation of cellular response to growth factor stimulus (`GO:0090287`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6dd66f2a73355a48dcca737e77521519c06c04b4aafdcbf06c54aeb268e0ce17`；疾病通路关联 ID `113d1608ed4f2fc5b8c99e2fd23ef1d95ba89da4c9c1fd90f1bdbd1a80763b63`。
- `PPARG` → negative regulation of locomotion (`GO:0040013`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ca11302ef511b71052d0946b90a33343b4f27093809a0cb215d08eaaa260e128`；疾病通路关联 ID `6139170bcab37c1207d6d6352d959f77bb99bd20b94afe4932e9306ecaf30772`。
- `PPARG` → negative regulation of angiogenesis (`GO:0016525`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `55b74e5d54a31a304c18269f9d362343b367621f581dfa1a087e7fce3ec84582`；疾病通路关联 ID `329f3715efc912c868c20f9da5e285ef19df0176f2d35ebe1a15d2560b21d42b`。
- `PPARG` → regulation of angiogenesis (`GO:0045765`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ec1dfbb5c4f955b4dd0b862a05460c18bb1744101210bcf9c49e4793daa9d24a`；疾病通路关联 ID `fd621a9075548c5edd7a1681b2b92bf81e1b72ac77bf76a96f9b0280943b5816`。
- `PPARG` → regulation of blood vessel endothelial cell migration (`GO:0043535`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0ebff8d72a195429b5a21125d5683bc7d14d1141aaebcf4900fd1700d61f9961`；疾病通路关联 ID `a60ac66d75840927ddefcec5a2adda1c2a6b78b133aa8ef5ec367af084e9331b`。
- `PPARG` → negative regulation of vasculature development (`GO:1901343`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6753b25d531cfc57f2221a348abb590a4d35279b65494d3d3ac7f9604ded62d1`；疾病通路关联 ID `724709f6cb596792000ed1e14b2ceb1a472a7962c99c412c0cbb474be1845f75`。
- `PPARG` → osteoblast differentiation (`GO:0001649`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `54cdbf7b77716cc02a1aa75ec591057dd1a782ee1062d856712e9cd03f4d7219`；疾病通路关联 ID `fb497d55381abddb56a55b0842d93ceec441c1a175f20d441eb2c6865a4c4487`。
- `PPARG` → vascular associated smooth muscle cell proliferation (`GO:1990874`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a55b6e47fddb4ef319ee3db9044db6d57d70358a7eaa6e38a65e2a6f07e0524d`；疾病通路关联 ID `795a0d0d29bede9cfa36bf4e9f6f4aca90e560cca94c71154dced6d43578a310`。
- `PPARG` → muscle cell proliferation (`GO:0033002`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `58ffc5954a665d7f5f6fa2e243cdcc799d6386f422b21759f462931712a05a77`；疾病通路关联 ID `5c128822fb19296e4ef26e66eafb63e455b18cec58afc65cfec37d9ed42b87d5`。
- `PPARG` → blood circulation (`GO:0008015`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `701706d086a2646afd647b508f9cc5ff73eab0b15bb297efed4ea0baf3278076`；疾病通路关联 ID `0bbba9e3e486b38c84c1f45032a5d0ba8f00a6fcc16ecebf9073058fe2508811`。
- `PPARG` → mitochondrial fission (`GO:0000266`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0027415152e767aed175d1cd2753805489b7c0e7bde6ec0542c105c6e0a48d57`；疾病通路关联 ID `c3021057f085ec4f670f9bf488f2f1705c4f91f74ff6eccc6d0d25b78c77a7b9`。
- `PPARG` → mitochondrion organization (`GO:0007005`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `30c9071a308329f3694f1420b4014a4a4ea4bc12f7321735b94e075db14b7544`；疾病通路关联 ID `91f16f83f9f1362d0c382e6ddaa2900ca7ab7efb03e0e19349590019a0bf952b`。
- `PPARG` → regulation of transmembrane receptor protein serine/threonine kinase signaling pathway (`GO:0090092`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ca72d47fa9b5457435f763e59658377db84441669620875fbcad091e90f2b11f`；疾病通路关联 ID `f66335b63e3f4b0c13e9d8cf21356787e0779f84d91a351e84e3c8b06627bab4`。
- `PPARG` → fatty acid metabolic process (`GO:0006631`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c0349f5a14089c7377787ca4ab56e59197fc4c61681302fc3922b585895cf0c8`；疾病通路关联 ID `fd71ef922c49921e7498b72e20cbc7fbed22798f8082c27bfe3c63e568a072ff`。
- `PPARG` → regulation of BMP signaling pathway (`GO:0030510`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `221b97894afd08ef5577bac3666c1c961663188caee8c22411f57b6cf2fd1789`；疾病通路关联 ID `e3b45c7d87f2362905bd0ab04ec0a4119e10502c0a1c05f4158326d4400b3dd0`。
- `PPARG` → lipid homeostasis (`GO:0055088`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `2a28657d6394061ee085c992c01fbe5997f5d75bfcd8e61c877d0750c4374b1d`；疾病通路关联 ID `679fff2ea6762f4b6ddf5b54234a190161d603cf212892956d44eb361720b11b`。
- `PPARG` → cellular response to transforming growth factor beta stimulus (`GO:0071560`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `425b975d0e10d929dd09aa356f90328bb569793da9eca01ca2355aadd40b44ac`；疾病通路关联 ID `01eba55e020bc5f3755382d5c927831c1cd858c0310f645d5c0decd3d1309a1f`。
- `PPARG` → response to BMP (`GO:0071772`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `570c0dbf30bbaf7308b18457716c198583137fb0679da1b764d7d350d1bfc250`；疾病通路关联 ID `4400b08e35f9dc29cf4183008fa98d8bbd92121c0faa2ca536a1057a78dc7bca`。
- `PPARG` → regulation of fat cell differentiation (`GO:0045598`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `e87fd51bccefea05162500e1a5ab568b8a8e2dac6fbd156aab33f2acb6a3a8b2`；疾病通路关联 ID `3703e4f48d6c6f7ce4a7dc04685bb6150ca5696c08a5ae34afe82cad49d20c86`。
- `PPARG` → positive regulation of fat cell differentiation (`GO:0045600`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d9de698d7d6a0e1a879a6a08842643d80dbd071d933475d0b135a2c1b45ce5ca`；疾病通路关联 ID `b24950d381ec2e55f48d263be7989a6b23cc1d490f6c4543e3ebbf4a918af31b`。
- `PPARG` → regulation of vascular associated smooth muscle cell proliferation (`GO:1904705`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d9c587e75c757a4ea4c91ae51f554a4f36410866793949fd5fac35508e5b6737`；疾病通路关联 ID `74bc45139cbafcd7a45f21c4ae67f6b5fd3cf9a24e37d4811a0b39cdae60451c`。
- `PPARG` → response to insulin (`GO:0032868`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `cc63275ca7458c59c7a55fcc325971ffd151ce28449264e808efc1bfa40da7d0`；疾病通路关联 ID `9a9eb82c6eb87c15b8e55a8abbeadb62bcf1bbfc01c0d14db53dd039e356f0c3`。
- `PPARG` → negative regulation of blood vessel morphogenesis (`GO:2000181`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `dde7893b33da18c509cb371d6dfcf3fdaf7ceb9b8439f34f472e20cadc63faa8`；疾病通路关联 ID `26fd9ee0347ea6811506ebfb1dfb6050fd7e44d3eb0bb034403396fad8683520`。
- `PPARG` → blood vessel endothelial cell migration (`GO:0043534`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `3f8e98ec33a9f29079cd922e54d7a1cd3e6b6bb61499bb3f9db5d8fe128a5eae`；疾病通路关联 ID `50ba80f9b9af0d7dce2b118c3a9a569cdfb3cfc31d71b4a121923ccb9f4752fa`。
- `PPARG` → negative regulation of vascular associated smooth muscle cell proliferation (`GO:1904706`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `52add0aaeb0b1d79b8893e2f9000f617333cea11e4e7adb5c313ee8f376bb490`；疾病通路关联 ID `4a25c08fb53e02a2c30b06fbf4e0de576a3a1162f6b1e96d650b71aba032e593`。
- `PPARG` → response to decreased oxygen levels (`GO:0036293`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9d3c0e7396559ca9f4181f18330653c1ffac3f58485c042dc33163406714cab2`；疾病通路关联 ID `bff18f6e7b48c048d68d23df1a3bb5e1d31044fae3f22719806a1c5ad2fc07e5`。
- `PPARG` → transforming growth factor beta receptor signaling pathway (`GO:0007179`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `a30afaf01a29f208518d88d360d3212588711c62f34d9ca08557509d53861da1`；疾病通路关联 ID `4c923527f7038bc20b364ba25ed9d0095b60e7a09a4e984668165f68d6bf2ac0`。
- `PPARG` → cellular ketone metabolic process (`GO:0042180`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `ff8e80df4af2db715e30aba01ff046f2b16b026fe78d3ea27c617f0618b48ceb`；疾病通路关联 ID `8bd7c249ab23302ceae2e3d18e3fcb6dbfb7f90b0e409bd0ae0927553cd41180`。
- `PPARG` → wound healing (`GO:0042060`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `b0a81504bfc0c96c7865cef5f5b52f64ae9291db55ea7608fa19f262c3d02026`；疾病通路关联 ID `65d248b22850e6a10bf2f8aab3db81986c63422a09c93bfdbace10642781baed`。
- `PPARG` → epithelial cell proliferation (`GO:0050673`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `070b77574a329cf38f785178263e6562ba8df8952f9bac1eb5d75f1fae45e885`；疾病通路关联 ID `2b2df3c276167dd52de61de430ba76c64ad2ff635c0a1b927dea816368f76fc6`。
- `PPARG` → cell surface receptor protein serine/threonine kinase signaling pathway (`GO:0007178`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c740565f2ab6b45d3fcb9998ce0216c7b8b7e9d27b5fd5f0f6d990591b64c068`；疾病通路关联 ID `0512826138d0e040bdb3c83956e0027f9c592ceadcbdde541f61e189ce34a1d9`。
- `PPARG` → myeloid leukocyte differentiation (`GO:0002573`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `b82664deea9df160c68c3f484f9b57f2ac6999d26fa231197a3cb346b0970c99`；疾病通路关联 ID `07ca32c37a6e75e69cd361371725af88d0d159abd124e78d41cc10f173caa4ca`。
- `PPARG` → transforming growth factor beta receptor superfamily signaling pathway (`GO:0141091`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f9fa827e07464f6bb479481927756d6fb70228fea3ce0111d64ea24001d0dbc3`；疾病通路关联 ID `bb5ee6294798345815a90c9a00515fdfcbc38a80a1b3bd3d094399c90e996959`。
- `PPARG` → SMAD protein signal transduction (`GO:0060395`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9745e53deabb7787007f1d24903f309404652abf4fb40f2779747ebdce3276ed`；疾病通路关联 ID `83bd32692e54ffc2610ba48e041088d2c2a5764febd038138c436aed63a9f5d4`。
- `PPARG` → BMP signaling pathway (`GO:0030509`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `9903eca3993f8555f9e459d5244d951646fa13d5be9844645a40f910968fce36`；疾病通路关联 ID `98e82478fbf47b9667d1cd742dc979364cedbba95e72c38fab962530ed48e2c4`。
- `PPARG` → lipid storage (`GO:0019915`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0c4cfd2cf487a5bbc16692adba57ba93bbaa925785708c5b49a8086c19fd1433`；疾病通路关联 ID `719d3ed9b46e45ba67301f28d1fd0633c5ff11ca2ecda071d8c3704bac794bbd`。
- `PPARG` → response to oxygen levels (`GO:0070482`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c9850fc4f240a97a7886aea842e94285ecde0fdd41843717d5eef7c245b093a8`；疾病通路关联 ID `0a45db29ea5d5f68ddb395bdbe994b8fb5fed8058986287b6a199c31c140a8a4`。
- `PPARG` → regulation of sequestering of triglyceride (`GO:0010889`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `01703de61f917393aed8198b94b4b447b0bf20a169372ccfe9017b8247925058`；疾病通路关联 ID `67d1231f066fcb2dd52f69ae780fe2ece8d2f3a29e4d80262d353f8d627c3589`。
- `PPARG` → regulation of endothelial cell migration (`GO:0010594`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `dce1aa92bd0864ca3dbb1609af2fde612dfb6143d1827a4b7e48931d7835a903`；疾病通路关联 ID `44b6f215656186368b386d7c2c0f0e740a25a47807f667e1b302c48e475df601`。
- `PPARG` → positive regulation of lipid metabolic process (`GO:0045834`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `95d9f397db2d530bd6d6874fdb110631cec5f36bb63a1155b0f1add8f043a8ec`；疾病通路关联 ID `7081d899f5dbf161581b18263e67b536bba9f5213c14e392351cd4da26aa75a9`。
- `PPARG` → response to peptide hormone (`GO:0043434`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `aacdcbf40b151e46a5739cafd9e01fd10e40e84eda4d1130691b0e1ae8f0e61c`；疾病通路关联 ID `1dde14a49e5d2ed73349ad0c18ac29dbe5193ee580250cffacef76d66b2bdc63`。
- `PPARG` → negative regulation of response to external stimulus (`GO:0032102`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `5336674f88ee52a456b800b5a4e2f4def4173978f569425ef257f766c7d93957`；疾病通路关联 ID `ce602b69bb0f10967100d2c27ad49a7c2dc3f32a049ab21cae52a478dc87ea6b`。
- `PPARG` → negative regulation of cell motility (`GO:2000146`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `fafe6e71d5c4755a64b86bda2ee5c257d47f3ad5a02315cd6b148e2d3218fdf4`；疾病通路关联 ID `cfe56607b83cc19b5b3f42df4c2cc322f360aa7c3ed6bfcacd8582d50dada818`。
- `PPARG` → connective tissue development (`GO:0061448`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `d17136e4d8bfbce7ac65d97157e2d522ce66eaf136057b1576d8e358963a820d`；疾病通路关联 ID `69afdf7705443ac74abbdbe55911fc10d943e9914efc9ae38b7ec3ec8f9f4560`。
- `PPARG` → response to nutrient levels (`GO:0031667`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `0a96a1e804359457fc21cdb8d30006c951550f0978d8c202054924b70968851d`；疾病通路关联 ID `405bb6061284d8bf5de468eb631870634d8e2fb9052656a541d71edf4d78a8ef`。
- `PPARG` → regulation of smooth muscle cell proliferation (`GO:0048660`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `364611856c82a4c8aee432aaf667472d325a992cf6fe519e3a645174b059af80`；疾病通路关联 ID `58b7602acf0408d496dde3c5533a522bc76c0f988a14233a9a2f33d8f47d0387`。
- `PPARG` → response to hypoxia (`GO:0001666`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `c2b71a1f057c6f7f1eb33599accaf1ced6d64fcddbcc5ba37edeec327a2ca0dd`；疾病通路关联 ID `f09d1eae7bc189a820971f26a6b7b752908b443169a15fe7708d6fbbbebba181`。
- `PPARG` → HALLMARK_CHOLESTEROL_HOMEOSTASIS (`MSIGDB:HALLMARK_CHOLESTEROL_HOMEOSTASIS`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `f7c2c9c9b73fb0782764e5f16427e0a59e0e8d38de8edcbd85b70ee9952971c2`；疾病通路关联 ID `056fd3ca3155b2c5ced562f8a292c3c77ee707b322d58bcf881caf4c850fdbd2`。
- `PPARG` → HALLMARK_UV_RESPONSE_DN (`MSIGDB:HALLMARK_UV_RESPONSE_DN`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `bbcc8847ec3561cd2ae4bfcdb1808a3feaa513ef4419f9f09cbc558c003f096c`；疾病通路关联 ID `bf648f1737f01dc9180b77ac5d98976b9adb1a68f463bb1c6a1d0796ed5dd571`。
- `PPARG` → HALLMARK_ADIPOGENESIS (`MSIGDB:HALLMARK_ADIPOGENESIS`)，S1方向=DOWN，GO/Reactome/Hallmark证据 ID `6c46624545b8fd573967a90fc6fb833178343b0116898ede32247c405eb0e66c`；疾病通路关联 ID `a2f092cb0e0e742c07755ed5fa0297e0140e5968540531bb7ba2cd940681e0cb`。

当前 S1 富集摘要：肿瘤上调侧突出 DNA replication、E2F/G2M 与 estrogen-response Hallmark；肿瘤下调侧突出氧化代谢、呼吸链/oxidative phosphorylation、脂肪酸代谢等。富集与路径重叠仅为注释关联，不是通路因果证明。

## 独立验证、机制假设与冲突证据

- Exp010 独立队列同条件排名：40.0；外部 S1 条件级排序与主排序总体 Spearman=0.544，Top10 重合仅 1/10。
- PRISM ER+ 平均敏感性：0.11547362867406667，细胞系数=9.0；PRISM 相关性弱且没有显示 ER+ 选择性，不能作为 S2 药效确认。
- 候选机制摘要：图谱记录 PPARG 部分激动作用，PPARG 在 S1 下调并关联代谢路径；激动作用并不能简单解释为表达逆转，机制方向存在不确定性。
- 文献链接：[https://pubmed.ncbi.nlm.nih.gov/22372600/](https://pubmed.ncbi.nlm.nih.gov/22372600/)。
- 本项目用确定性证据模板整理解释；未调用 LLM 生成本候选机制正文，因此不把模板内容标为 AI 输出。

## 局限

该药主条件仅由 1 条 LINCS signature 支持。WTCS 是表达逆关联，不等同药效。靶点关系与机制文献可能来自一般药理，不代表在 ER 阳性乳腺癌中直接成立。当前图谱没有可审计 PPI 边；不推断一层 PPI 扩展。后续需要多签名/剂量的重复、ER+ 模型剂量反应、正常细胞对照和机制实验。

## 可追溯文件

- S2 原始评分：`results/final_signature_scores.csv`（signature ID 可检索）；候选证据：`results/final_top10_evidence_matrix.csv`。
- 图谱关系路径：`mechanism/top10_mechanism_paths.csv`；原始图谱查询结果：`mechanism/final_neo4j_direct_targets.csv`、`mechanism/final_neo4j_s1_pathway_links.csv`。
- 逐条引用登记：`mechanism/top10_evidence_citations.csv`。
