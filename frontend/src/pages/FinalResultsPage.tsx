import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Button, Card, Col, Collapse, Descriptions, Divider, Image, Modal, Row, Space, Spin, Statistic, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { api } from '../api'
import { useProject, Loading } from '../projectContext'
import { palette } from '../designTokens'

const { Title, Text, Paragraph } = Typography

type Candidate = {
  rank: number
  pert_id: string
  drug_name: string
  WTCS_median: number
  reversal_score_project_convention: number
  n_signatures: number
  n_24h_dose_conditions: number
  negative_dose_fraction: number
  external_S1_same_condition_rank: number | null
  PRISM_ERpos_mean_sensitivity: number | null
  PRISM_ERpos_cell_lines: number | null
  Neo4j_exact_InChIKey_status: string
  Neo4j_direct_target_count: number
  Neo4j_target_genes: string
  S1_DEG_direct_target_count: number
  S1_UP_direct_targets: string
  S1_DOWN_direct_targets: string
  Neo4j_target_to_S1_pathway_rows: number
  Neo4j_S1_pathways: string
  target_S2_compz_measured: number
  target_S2_opposite_direction_count: number
  target_S2_same_direction_count: number
  mechanism_evidence_limit: string
  target_expression_caveat: string
  literature_links: string
  mechanism_summary: string
  target_evidence_ids_list: string[]
  mechanism_paths: Array<{
    target_symbol: string
    target_gene_id: string
    pathway_id: string
    pathway_label: string
    s1_direction: string
    s1_logFC: number | null
    s1_FDR: number | null
    target_evidence_ids: string[]
    pathway_evidence_ids: string[]
    disease_context_evidence_ids: string[]
  }>
}

type AuditCandidate = {
  rank: number; drug_name: string; pert_id: string; sig_id: string; WTCS: number
  distil_cc_q75: number; tas: number; level5_consensus_signatures: number
  formal_scored_consensus_signatures: number; replicate_instances: number
  negative_dose_count: number; dose_conditions: number
  historical_B200_p: number | null; historical_B200_fdr: number | null
  historical_B200_score_matches_current: boolean
  PRISM_ERpos_mean: number | null; PRISM_ERpos_lines: number | null
}

type Final05Audit = {
  frozen_top10: AuditCandidate[]
  historical_permutation_note: string
  validation_priorities: Array<{ drug_name: string; role: string }>
  special_cautions: string[]
}

type FinalData = {
  project_id: string
  graph_build_id?: string
  status: string
  protocol: string
  ranking_caveat: string
  candidates: Candidate[]
  evidence_priority: Array<Record<string, string | number>>
  final05: Final05Audit
}

const loadFinalData = async (): Promise<FinalData> => {
  const [response, auditResponse] = await Promise.all([fetch('/final-results.json'), fetch('/final05-audit.json')])
  if (!response.ok) throw new Error(`Final Results 数据读取失败：${response.status}`)
  if (!auditResponse.ok) throw new Error(`Final05 审计数据读取失败：${auditResponse.status}`)
  const base = await response.json() as Omit<FinalData, 'final05'>
  const final05 = await auditResponse.json() as Final05Audit
  return { ...base, final05 }
}

function protocolLabel(value: string) {
  if (value.startsWith('BING Top100 UP/DOWN; MCF7 trt_cp; 24 h; CC≥0.2; maximum-coverage dose; WTCS median per pert_id/condition')) {
    return '疾病签名采用 BING 空间内 Top100 上调/下调基因；LINCS 条件为 MCF7、化学药物扰动、24 小时且 CC≥0.2。主剂量按合格条件中覆盖药物最多的规则确定；WTCS 在每个药物与条件内取中位数。'
  }
  return value
}

function rankingCaveatLabel(value: string) {
  if (value.startsWith('WTCS<0 is inverse expression association')) {
    return 'WTCS < 0 表示药物扰动表达与疾病表达呈反向关联，不能据此判定药物有效。知识图谱、PRISM 与外部证据不参与 S2 排名。'
  }
  return value
}

function auditNoteLabel(value: string) {
  if (value.startsWith('Exp008 B200, 2,000 次置换统计结果')) {
    return 'Exp008 B200 的 2,000 次置换统计为历史结果。只有当前 WTCS 与当时观测值精确一致的条目才标记为匹配；其余显示“无可比结果”。'
  }
  if (value.startsWith('Exp008 B200 2,000-permutation statistics are historical')) {
    return 'Exp008 B200 的 2,000 次置换统计为历史结果。只有当前 WTCS 与当时观测值精确一致的条目才标记为匹配；其余显示“无可比结果”。'
  }
  return value
}

const loadEvidenceRecord = async (evidenceId: string, graphBuildId?: string): Promise<Record<string, unknown>> => {
  try {
    return await api.evidence(evidenceId, graphBuildId)
  } catch (apiError) {
    const response = await fetch('/final-evidence-records.json')
    if (response.ok) {
      const records = await response.json() as Record<string, Record<string, unknown>>
      if (records[evidenceId]) return records[evidenceId]
    }
    throw apiError
  }
}

const recordObject = (value: unknown): Record<string, unknown> =>
  value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}

const recordText = (value: unknown) => typeof value === 'string' && value.trim() ? value : '未提供'

function EvidenceRecordDetails({ record, evidenceId }: { record: Record<string, unknown>; evidenceId: string }) {
  const assertion = recordObject(record.source_assertion)
  const sources = recordObject(assertion.sources)
  const relations = Array.isArray(assertion.relation_assertions) ? assertion.relation_assertions.map(recordObject) : []
  const rawUrls = assertion.source_urls ?? record.source_url
  const urls = Array.isArray(rawUrls) ? rawUrls.filter((url): url is string => typeof url === 'string') : typeof rawUrls === 'string' ? [rawUrls] : []
  return <Space direction="vertical" size={14} style={{ width: '100%' }}>
    <Descriptions bordered size="small" column={{ xs: 1, md: 2 }}>
      <Descriptions.Item label="证据 ID"><Text code copyable>{evidenceId}</Text></Descriptions.Item>
      <Descriptions.Item label="来源版本">{recordText(record.source_release)}</Descriptions.Item>
      <Descriptions.Item label="来源记录">{recordText(record.source_record_id)}</Descriptions.Item>
      <Descriptions.Item label="图谱版本">{recordText(record.graph_build_id)}</Descriptions.Item>
      <Descriptions.Item label="直接来源">{Array.isArray(sources.direct) ? sources.direct.join('、') : '未提供'}</Descriptions.Item>
      <Descriptions.Item label="间接来源">{Array.isArray(sources.indirect) ? sources.indirect.join('、') : '未提供'}</Descriptions.Item>
    </Descriptions>
    <div>
      <Text strong>关系断言</Text>
      <div style={{ marginTop: 8 }}>{relations.length ? relations.map((item, index) => <Tag key={`${String(item.relation)}-${index}`}>{recordText(item.relation)} · {recordText(item.source)}</Tag>) : <Text type="secondary">该记录未提供结构化关系断言。</Text>}</div>
    </div>
    <div>
      <Text strong>原始来源链接</Text>
      <div style={{ marginTop: 6 }}>{urls.length ? urls.map((url) => <div key={url}><a href={url} target="_blank" rel="noreferrer">{url}</a></div>) : <Text type="secondary">该图谱记录未附可直接访问的原始 URL；可按来源版本和来源记录 ID 回查。</Text>}</div>
    </div>
    <Collapse items={[{ key: 'raw', label: '查看原始证据 JSON', children: <pre style={{ maxHeight: 360, overflow: 'auto', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(record, null, 2)}</pre> }]} />
  </Space>
}

export default function FinalResultsPage() {
  const { project, isLoading, error } = useProject()
  const query = useQuery({ queryKey: ['final-results'], queryFn: loadFinalData, staleTime: 60_000 })
  const [selectedId, setSelectedId] = useState<string>()
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string>()
  const evidenceQuery = useQuery({
    queryKey: ['final-result-evidence', project?.project_id, selectedEvidenceId, query.data?.graph_build_id],
    queryFn: () => loadEvidenceRecord(selectedEvidenceId!, query.data?.graph_build_id),
    enabled: !!project && !!selectedEvidenceId,
  })

  if (isLoading) return <Loading />
  if (error) return <Loading error={error as Error} />
  if (!project || project.slug !== 'erpos-gse42568') {
    return <Alert type="warning" showIcon message="这组最终结果属于 GSE42568 ER 阳性乳腺癌项目" description="请在顶部项目选择器中切换到 erpos-gse42568，再查看该项目的 Top 10。其他项目不会复用这组候选。" />
  }
  if (query.isLoading) return <Loading />
  if (query.error) return <Loading error={query.error as Error} />

  const data = query.data!
  const candidates = data.candidates
  const selected = candidates.find((item) => item.pert_id === selectedId) ?? candidates[0]
  const columns: ColumnsType<Candidate> = [
    { title: '排名', dataIndex: 'rank', width: 70, sorter: (a, b) => a.rank - b.rank },
    { title: '候选药物', dataIndex: 'drug_name', width: 190, render: (value: string, row) => <Space direction="vertical" size={0}><Text strong>{value}</Text><Text type="secondary" style={{ fontSize: 11 }}>{row.pert_id}</Text></Space> },
    { title: 'WTCS', dataIndex: 'WTCS_median', width: 110, render: (value: number) => <Tag color={value < 0 ? 'blue' : 'volcano'}>{value.toFixed(3)}</Tag>, sorter: (a, b) => a.WTCS_median - b.WTCS_median },
    { title: '签名数', dataIndex: 'n_signatures', width: 90 },
    { title: '负 WTCS 剂量比例', dataIndex: 'negative_dose_fraction', width: 150, render: (value: number) => `${(value * 100).toFixed(0)}%` },
    { title: '外部 S1 排名', dataIndex: 'external_S1_same_condition_rank', width: 125, render: (value: number | null) => value == null ? '—' : Math.round(value) },
    { title: 'PRISM ER+ 敏感性', dataIndex: 'PRISM_ERpos_mean_sensitivity', width: 155, render: (value: number | null) => value == null ? '—' : value.toFixed(3) },
    { title: 'KG 靶点 / 路径', key: 'kg', width: 120, render: (_, row) => row.Neo4j_direct_target_count ? `${row.Neo4j_direct_target_count} / ${row.Neo4j_target_to_S1_pathway_rows}` : '未覆盖' },
    { title: '查看解释', key: 'action', fixed: 'right', width: 100, render: (_, row) => <Button size="small" onClick={(event) => { event.stopPropagation(); setSelectedId(row.pert_id) }}>查看证据</Button> },
  ]

  const priorityColumns = [
    { title: '机制证据查看顺序', dataIndex: 'evidence_coverage_only_order', width: 140 },
    { title: '候选药物', dataIndex: 'drug_name' },
    { title: 'S2 主排名', dataIndex: 'rank' },
    { title: '直接靶点', dataIndex: 'Neo4j_direct_target_count' },
    { title: 'S1 通路连接', dataIndex: 'Neo4j_target_to_S1_pathway_rows' },
  ]

  const auditColumns: ColumnsType<AuditCandidate> = [
    { title: '\u6392\u540d', dataIndex: 'rank', width: 64 },
    { title: '\u5019\u9009\u836f\u7269', dataIndex: 'drug_name', width: 140 },
    { title: '签名 ID', dataIndex: 'sig_id', width: 205, render: (v: string) => <Text code>{v}</Text> },
    { title: 'WTCS', dataIndex: 'WTCS', width: 90, render: (v: number) => v.toFixed(3) },
    { title: 'CC q75', dataIndex: 'distil_cc_q75', width: 90 },
    { title: '\u5e95\u5c42\u5b9e\u4f8b / \u8ba1\u5206\u5171\u8bc6\u7b7e\u540d', width: 165, render: (_, r) => `${r.replicate_instances} / ${r.formal_scored_consensus_signatures}${r.level5_consensus_signatures > r.formal_scored_consensus_signatures ? ` (${r.level5_consensus_signatures} \u6761\u5143\u6570\u636e\u7b7e\u540d)` : ''}` },
    { title: '\u8d1f WTCS \u5242\u91cf\u6570', width: 120, render: (_, r) => `${r.negative_dose_count}/${r.dose_conditions}` },
    { title: '\u5386\u53f2 B200 p / FDR', width: 150, render: (_, r) => r.historical_B200_score_matches_current && r.historical_B200_p != null ? `${r.historical_B200_p.toPrecision(3)} / ${r.historical_B200_fdr?.toPrecision(3)}` : '无可比结果' },
    { title: 'PRISM ER+', width: 120, render: (_, r) => r.PRISM_ERpos_mean == null ? '暂无数据' : `${r.PRISM_ERpos_mean.toFixed(3)} (n=${r.PRISM_ERpos_lines})` },
  ]

  const links = (selected.literature_links ?? '').split(';').filter(Boolean)
  const showList = (value: string) => value?.split(';').filter(Boolean).join('、') || '当前数据中无可列出的条目'

  return <>
    <div className="page-heading">
      <div>
        <Text className="eyebrow">最终结果 / Final01–05</Text>
        <Title level={2}>ER 阳性乳腺癌 Top 10 候选药物</Title>
        <Text type="secondary">疾病表达特征 → LINCS 药物扰动特征 → 可追溯机制证据</Text>
      </div>
      <Space wrap>
        <a className="toolbar-button" href="/final-top10.csv" download>下载 Top10 CSV</a>
        <a className="toolbar-button" href="/final-evidence-matrix.csv" download>下载证据矩阵</a>
        <a className="toolbar-button" href="/final-pathways.json" download>下载机制路径</a>
        <a className="toolbar-button" href="/final05-scientific-audit-report.md" download>下载 Final05 审计报告</a>
        <a className="toolbar-button" href="/final05-evidence-grade.csv" download>下载分项证据表</a>
        <a className="toolbar-button" href="/final05-dose-support.csv" download>下载剂量支持表</a>
        <a className="toolbar-button" href="/final05-dose-metadata-qc.csv" download>下载全剂量 QC 表</a>
        <a className="toolbar-button" href="/final05-all-signatures.csv" download>下载全部签名分数</a>
        <a className="toolbar-button" href="/final05-identifier-audit.csv" download>下载 ID 核查表</a>
      </Space>
    </div>

    <Alert className="section-card" type="warning" showIcon message="这是表达逆转筛选候选，不是疗效结论" description={`${rankingCaveatLabel(data.ranking_caveat)} ${protocolLabel(data.protocol)}`} />

    <Card className="section-card" title="Final05 科研可靠性复核">
      <Alert type="info" showIcon message="一条 Level 5 共识签名不等于一次独立队列重复" description="主条件签名整合底层 L1000 实例谱。Iniparib 另有一条原始元数据签名因 CC q75 < 0.2 未进入正式评分。历史 B200 置换值只对当前 WTCS 对齐的行显示；NA 表示没有可比的历史结果。" style={{ marginBottom: 12 }} />
      <Table<AuditCandidate> rowKey="pert_id" size="small" dataSource={data.final05.frozen_top10} columns={auditColumns} pagination={false} scroll={{ x: 1100 }} />
      <Paragraph type="secondary" style={{ marginTop: 12 }}>{auditNoteLabel(data.final05.historical_permutation_note)}</Paragraph>
      <Paragraph><Text strong>建议后续验证：</Text>{data.final05.validation_priorities.map(x => `${x.drug_name}：${x.role}`).join(' · ')}</Paragraph>
      {data.final05.special_cautions.map(caution => <Alert key={caution} type="warning" showIcon message={caution} style={{ marginTop: 8 }} />)}
    </Card>

    <Row gutter={[14, 14]} className="section-card">
      <Col xs={12} md={6}><Card><Statistic title="修正后 S2 签名" value={5861} /></Card></Col>
      <Col xs={12} md={6}><Card><Statistic title="主剂量唯一候选" value={1032} suffix="个" /></Card></Col>
      <Col xs={12} md={6}><Card><Statistic title="Top10 有精确 KG 药物节点" value={5} suffix="/10" /></Card></Col>
      <Col xs={12} md={6}><Card><Statistic title="Top10 有 PRISM ER+ 结果" value={5} suffix="/10" /></Card></Col>
    </Row>

    <Card className="section-card" title="Top 10 排名 · 选择药物查看逐药解释">
      <Table<Candidate> rowKey="pert_id" size="small" dataSource={candidates} columns={columns} pagination={false} scroll={{ x: 1120 }} onRow={(row) => ({ onClick: () => setSelectedId(row.pert_id), style: { cursor: 'pointer', background: row.pert_id === selected.pert_id ? palette.accentWash : undefined } })} />
      <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>固定规则：BING Top100 UP/DOWN；MCF7、24 h、CC≥0.2；10 μM 是合格剂量中覆盖药物数最多的统一条件；同一药物按该条件内 signature WTCS 中位数排序。不会为每种药物挑最有利剂量。</Paragraph>
    </Card>

    <Card className="section-card" title={`${selected.rank}. ${selected.drug_name} · 机制证据摘要`}>
      <Alert
        type={selected.Neo4j_direct_target_count > 0 ? 'success' : 'warning'}
        showIcon
        message={selected.Neo4j_direct_target_count > 0 ? '本项目知识图谱有精确药物映射' : '本项目知识图谱未精确映射该药物'}
        description={selected.Neo4j_direct_target_count > 0
          ? `图谱记录 ${selected.Neo4j_direct_target_count} 个直接靶点，其中 ${selected.S1_DEG_direct_target_count} 个与 S1 差异基因相交，并形成 ${selected.Neo4j_target_to_S1_pathway_rows} 条靶点—S1 通路关联。关联数量不等于独立验证数量。`
          : '该候选没有当前 GraphBuild 内可追溯的直接靶点或 S1 通路路径。下方文献仅提供药物的一般药理背景，不是本项目图谱证据。'}
        style={{ marginBottom: 14 }}
      />
      <Descriptions bordered size="small" column={{ xs: 1, md: 2 }}>
        <Descriptions.Item label="主条件 WTCS">{selected.WTCS_median.toFixed(4)}；负值表示表达逆关联</Descriptions.Item>
        <Descriptions.Item label="合格 signature 数">{selected.n_signatures}</Descriptions.Item>
        <Descriptions.Item label="24 h 剂量条件">{selected.n_24h_dose_conditions} 个；{(selected.negative_dose_fraction * 100).toFixed(0)}% 条件 WTCS 为负</Descriptions.Item>
        <Descriptions.Item label="图谱药物匹配">{selected.Neo4j_exact_InChIKey_status}</Descriptions.Item>
        <Descriptions.Item label="直接靶点">{selected.Neo4j_direct_target_count} 个；{showList(selected.Neo4j_target_genes)}</Descriptions.Item>
        <Descriptions.Item label="S1 上调的直接靶点">{showList(selected.S1_UP_direct_targets)}</Descriptions.Item>
        <Descriptions.Item label="S1 下调的直接靶点">{showList(selected.S1_DOWN_direct_targets)}</Descriptions.Item>
        <Descriptions.Item label="S1 通路连接">{selected.Neo4j_target_to_S1_pathway_rows} 条；{showList(selected.Neo4j_S1_pathways)}</Descriptions.Item>
        <Descriptions.Item label="目标基因 COMPZ">测到 {selected.target_S2_compz_measured} 个；相对 S1 方向相反 {selected.target_S2_opposite_direction_count} 个、相同 {selected.target_S2_same_direction_count} 个（描述性）</Descriptions.Item>
        <Descriptions.Item label="独立证据">Exp010 同条件排名：{selected.external_S1_same_condition_rank == null ? '暂无匹配' : Math.round(selected.external_S1_same_condition_rank)}；PRISM ER+：{selected.PRISM_ERpos_mean_sensitivity == null ? '暂无数据' : selected.PRISM_ERpos_mean_sensitivity.toFixed(3)}</Descriptions.Item>
      </Descriptions>
      <Paragraph style={{ marginTop: 16 }}>{selected.mechanism_summary}</Paragraph>
      <Alert type="info" showIcon message="证据边界" description={`${selected.mechanism_evidence_limit === 'Current graph has no exact InChIKey node' ? '当前知识图谱没有精确 InChIKey 匹配。' : '知识图谱路径表示有来源的关联，不证明因果或治疗效果。'} ${selected.target_expression_caveat}`} />
      {selected.mechanism_paths?.some((path) => path.s1_direction) && <>
        <Divider titlePlacement="start">靶点与 S1 差异基因的交集</Divider>
        <Table
          size="small"
          rowKey="target_gene_id"
          pagination={false}
          dataSource={Array.from(new Map(selected.mechanism_paths.filter((path) => path.s1_direction).map((path) => [path.target_gene_id, path])).values())}
          columns={[
            { title: '靶点基因', dataIndex: 'target_symbol' },
            { title: 'S1 方向', dataIndex: 's1_direction', render: (value: string) => <Tag color={value === 'UP' ? 'volcano' : 'blue'}>{value === 'UP' ? '肿瘤上调' : '肿瘤下调'}</Tag> },
            { title: 'logFC（Tumor − Normal）', dataIndex: 's1_logFC', render: (value: number | null) => value == null ? '—' : value.toFixed(3) },
            { title: 'FDR', dataIndex: 's1_FDR', render: (value: number | null) => value == null ? '—' : value.toExponential(2) },
            { title: '路径示例', key: 'path', render: (_, row) => row.pathway_label || '暂无关联通路' },
          ]}
        />
      </>}
      {!!selected.target_evidence_ids_list?.length && <Paragraph style={{ marginTop: 12 }}>
        药物靶点来源记录：{selected.target_evidence_ids_list.slice(0, 12).map((id) => <Button key={id} size="small" type="link" onClick={() => setSelectedEvidenceId(id)}>Evidence {id.slice(0, 10)}…</Button>)}
        {selected.target_evidence_ids_list.length > 12 && <Text type="secondary">另有 {selected.target_evidence_ids_list.length - 12} 条，见下载证据矩阵。</Text>}
      </Paragraph>}
      <Card size="small" style={{ marginTop: 14 }} title={`当前图谱中的靶点 → S1 通路路径（${selected.mechanism_paths?.length ?? 0} 条）`}>
        {selected.mechanism_paths?.length ? <Table
          rowKey={(row, index) => `${row.target_gene_id}-${row.pathway_id}-${index}`}
          size="small" pagination={{ pageSize: 6 }} dataSource={selected.mechanism_paths}
          columns={[
            { title: '靶点', dataIndex: 'target_symbol', width: 100 },
            { title: 'S1 方向 / FDR', key: 's1', width: 145, render: (_, row) => `${row.s1_direction || '—'} / ${row.s1_FDR == null ? '—' : row.s1_FDR.toPrecision(3)}` },
            { title: 'S1 富集通路', dataIndex: 'pathway_label', render: (value: string, row) => <Space direction="vertical" size={0}><Text>{value}</Text><Text type="secondary">{row.pathway_id}</Text></Space> },
            { title: '原始 Evidence ID', key: 'evidence', width: 210, render: (_, row) => {
              const ids = [...new Set([...row.target_evidence_ids, ...row.pathway_evidence_ids, ...row.disease_context_evidence_ids])]
              return ids.length ? <Space wrap>{ids.slice(0, 3).map((id) => <Button key={id} size="small" type="link" onClick={() => setSelectedEvidenceId(id)}>{id.slice(0, 10)}…</Button>)}</Space> : '—'
            } },
          ]}
        /> : <Text type="secondary">当前 GraphBuild 没有与该候选相连的可审计路径。外部文献只作为一般药理背景，不显示为项目图谱路径。</Text>}
      </Card>
      {!!links.length && <Paragraph style={{ marginTop: 12 }}>药物一般机制来源：{links.map((url, index) => <span key={url}>{index > 0 ? ' · ' : ''}<a href={url} target="_blank" rel="noreferrer">文献 {index + 1}</a></span>)}</Paragraph>}
    </Card>

    <Card className="section-card" title="机制证据查看顺序（不改变 S2 排名）">
      <Paragraph type="secondary">这里只按当前图谱中的靶点和 S1 通路材料是否齐全安排人工查看顺序；它不是新的候选排名，也不代表药物更有效。</Paragraph>
      <Table rowKey="pert_id" size="small" pagination={false} dataSource={data.evidence_priority} columns={priorityColumns} />
    </Card>

    <Card className="section-card" title="实验图表">
      <Space direction="vertical" size={20} style={{ width: '100%' }}>
        <Image src="/final_top10_wtcs.png" alt="Top10 WTCS 排名图" />
        <Image src="/final_top10_dose_sensitivity.png" alt="不同剂量 WTCS 热图" />
        <Image src="/final_evidence_coverage.png" alt="Top10 证据覆盖图" />
      </Space>
    </Card>

    <Modal title="可追溯来源证据" open={!!selectedEvidenceId} onCancel={() => setSelectedEvidenceId(undefined)} footer={null} width={820}>
      {evidenceQuery.isLoading ? <Spin /> : evidenceQuery.error ? <Alert type="error" showIcon message="证据读取失败" description={(evidenceQuery.error as Error).message} /> : <EvidenceRecordDetails record={evidenceQuery.data ?? {}} evidenceId={selectedEvidenceId ?? ''} />}
    </Modal>
  </>
}
