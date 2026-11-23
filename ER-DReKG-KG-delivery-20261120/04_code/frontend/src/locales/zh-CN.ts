export const zhCN = {
  navigation: [
    { to: '/', icon: '⌂', label: '项目总览', end: true },
    { to: '/s1', icon: 'S1', label: 'S1 疾病分析' },
    { to: '/s2', icon: 'S2', label: 'S2 药物筛选' },
    { to: '/graph', icon: 'KG', label: '知识图谱' },
    { to: '/drugs', icon: 'Rx', label: '机制证据' },
    { to: '/compare', icon: '↔', label: '可靠性分析' },
    { to: '/final-results', icon: '10', label: '最终研究结果' },
  ],
  common: {
    project: '研究项目', loading: '正在加载', noData: '暂无数据', export: '导出',
    retry: '重试', status: '状态', source: '数据来源', evidence: '证据',
    up: '上调', down: '下调', unknown: '未知',
  },
  status: {
    completed: '已完成', materialized: '已导入', importing: '导入中', materialized_snapshot: '已登记快照', failed: '失败', running: '运行中',
    pending: '待处理', partial: '部分完成', blocked: '受阻', queued: '排队中',
    active: '进行中', test_only: '仅软件测试', validated: '已验证',
    validation_pending: '待校验', imported: '已导入', not_started: '未开始',
    materializing: '正在导入',
  } as Record<string, string>,
  runType: {
    s1_precomputed_deg: 'S1 · 预计算差异表达', s1_limma_microarray: 'S1 · 芯片差异分析',
    s1_rnaseq_edger_voom: 'S1 · RNA-seq 差异分析', s1_pathway_enrichment: 'S1 · 通路富集',
    s2_lincs: 'S2 · LINCS 药物筛选', kg_graph_bundle: '知识图谱 · 证据包',
  } as Record<string, string>,
  pageTitle: {
    '/': '项目总览', '/s1': 'S1 疾病分析', '/s2': 'S2 药物筛选',
    '/graph': '知识图谱探索', '/drugs': '机制证据', '/compare': '可靠性分析',
    '/final-results': '最终研究结果',
  } as Record<string, string>,
} as const

export function statusLabel(value?: string) {
  return value ? zhCN.status[value] ?? value : zhCN.common.unknown
}

export function runTypeLabel(value?: string) {
  return value ? zhCN.runType[value] ?? value : zhCN.common.unknown
}

export function identifierLabel(value?: string) {
  return ({ symbol: '基因符号', entrez: 'Entrez ID', ensembl: 'Ensembl ID' } as Record<string, string>)[value ?? ''] ?? value ?? zhCN.common.unknown
}

export function mappingStatusLabel(value?: string) {
  const labels: Record<string, string> = {
    matched_exact_inchikey_with_supported_path: '已精确匹配，并有支持路径',
    matched_exact_inchikey_no_supported_path: '已精确匹配，暂无支持路径',
    unmatched_no_exact_inchikey: '未找到精确 InChIKey 匹配',
    matched_exact_inchikey: '已精确匹配',
    no_exact_chemical_match: '未找到精确化学结构匹配',
    no_exact_match: '未找到精确匹配',
    high: '较高', moderate: '中等', low: '较低',
  }
  return value ? labels[value] ?? value : zhCN.common.unknown
}

export function graphTypeLabel(value?: string) {
  const labels: Record<string, string> = {
    Drug: '药物', Candidate: '候选药物', Gene: '基因', Protein: '蛋白质',
    Disease: '疾病', Pathway: '通路', BiologicalProcess: '生物过程',
    drug_target: '药物靶向', targets: '靶向', treats: '治疗关系',
    associated_with: '相关', participates_in: '参与', regulates: '调控',
    interacts_with: '相互作用',
  }
  return value ? labels[value] ?? value : zhCN.common.unknown
}

export function projectLabel(name: string, slug: string) {
  return slug === 'erpos-gse42568' ? 'ER 阳性乳腺癌药物重定位（GSE42568）' : name
}

export function contrastLabel(value?: string) {
  return value?.replace(/\bTumor\b/gi, '肿瘤').replace(/\bNormal\b/gi, '正常').replace(/\bvs\b/gi, '对比') ?? '比较方向未配置'
}

export function studyTitleLabel(accession: string, title: string) {
  return accession === 'GSE42568' && /breast cancer gene expression analysis/i.test(title)
    ? '乳腺癌基因表达分析'
    : title
}
