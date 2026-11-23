import { useMutation, useQuery } from '@tanstack/react-query'
import { Alert, Button, Card, Col, Collapse, Modal, Row, Select, Space, Spin, Statistic, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ElementDefinition } from 'cytoscape'
import { api, isGraphBuildQueryable } from '../api'
import { palette } from '../designTokens'
import { useProject } from '../projectContext'

const { Title, Text, Paragraph } = Typography

type FunnelStep = { step: string; n: number }
type Top20Row = {
  rank: number; drug: string; pert_id: string; S_disc: number; stability: number
  doses: number; chains: number; prism: string
}
type MechRow = {
  rank: number; drug: string; pert_id: string; rank_v4: number; S_disc: number
  chains: number; er_chains: number; targets: string; prism: string
}
type CoreRow = {
  rank: number; drug: string; pert_id: string; rank_v4: number; S_disc: number
  chains: number; prism: string
}
type Payload = {
  generated_utc: string; protocol: string; funnel: FunnelStep[]
  top20: Top20Row[]; mechanism_top10: MechRow[]; core_c: CoreRow[]; caveats: string[]
}
type LocalGraphNode = { id: string; label: string; kind: string; detail: Record<string, any> }
type LocalGraphEdge = { id: string; source: string; target: string; relation: string; category: string; evidence_ids: string[]; evidence: Record<string, any>[]; detail: Record<string, any>; synthetic?: boolean }
type LocalGraph = { status: string; ranking: Record<string, any>; graph: Record<string, any>; nodes: LocalGraphNode[]; edges: LocalGraphEdge[]; coverage: Record<string, any>; limits: string[] }

function RobustTop10Graph({ elements, centerId, onNode, onEdge }: { elements: ElementDefinition[]; centerId?: string; onNode: (node: LocalGraphNode) => void; onEdge: (edge: LocalGraphEdge) => void }) {
  const container = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!container.current) return
    let disposed = false
    let destroy: (() => void) | undefined
    void import('cytoscape').then(({ default: cytoscape }) => {
      if (disposed || !container.current) return
      const cy = cytoscape({
        container: container.current,
        elements,
        layout: centerId
          ? { name: 'concentric', animate: false, fit: true, padding: 48, minNodeSpacing: 24, avoidOverlap: true, spacingFactor: 0.9, concentric: (node: any) => node.id() === centerId ? 10000 : node.data('kind') === 'drug' ? 800 : node.data('kind') === 'gene' ? 500 : node.data('kind') === 'pathway' ? 100 : 0, levelWidth: () => 1 }
          : { name: 'cose', animate: false, fit: true, padding: 36, nodeRepulsion: 6500, idealEdgeLength: 92, edgeElasticity: 90, gravity: 0.18, numIter: 1200, randomize: true },
        minZoom: 0.12,
        maxZoom: 3,
        style: [
          { selector: 'node', style: { label: 'data(label)', color: '#344256', 'font-size': 8, 'min-zoomed-font-size': 5, 'text-wrap': 'wrap', 'text-max-width': '100px', 'text-outline-color': '#fff', 'text-outline-width': 1, width: 24, height: 24, 'background-color': '#8aa0b8' } },
          { selector: 'node.robust-candidate', style: { 'background-color': '#2377d4', shape: 'round-rectangle', width: 62, height: 44, color: '#10243b', 'font-size': 10, 'font-weight': 700 } },
          { selector: 'node.drug', style: { 'background-color': '#52a3a1', shape: 'round-rectangle', width: 42, height: 32, 'font-weight': 700 } },
          { selector: 'node.gene', style: { 'background-color': '#83b1e2', shape: 'ellipse', width: 30, height: 30, 'font-weight': 600 } },
          { selector: 'node.pathway', style: { 'background-color': '#b49bd7', shape: 'diamond', width: 26, height: 26, 'font-size': 7, 'text-max-width': '110px' } },
          { selector: 'edge', style: { width: 1.4, 'line-color': '#aab7c5', 'target-arrow-color': '#aab7c5', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', label: 'data(label)', color: '#596778', 'font-size': 6, 'text-background-color': '#fff', 'text-background-opacity': 0.9, 'text-background-padding': '1px' } },
          { selector: 'edge.candidate-mapping', style: { 'line-style': 'dashed', 'line-color': '#557fae', 'target-arrow-color': '#557fae' } },
          { selector: 'edge.drug-target', style: { width: 2.6, 'line-color': '#d47d42', 'target-arrow-color': '#d47d42' } },
          { selector: 'edge.target-pathway', style: { 'line-color': '#9274bd', 'target-arrow-color': '#9274bd' } },
          { selector: 'node:selected', style: { 'border-width': 3, 'border-color': '#f0a43c', 'z-index': 20 } },
          { selector: 'edge:selected', style: { width: 3.5, 'line-color': '#f0a43c', 'target-arrow-color': '#f0a43c', 'z-index': 20 } },
        ],
      })
      destroy = () => cy.destroy()
      cy.on('tap', 'node', event => {
        const data = event.target.data()
        try { onNode({ id: data.id, label: data.label, kind: data.kind, detail: JSON.parse(data.detail || '{}') }) } catch { onNode({ id: data.id, label: data.label, kind: data.kind, detail: {} }) }
      })
      cy.on('tap', 'edge', event => {
        const data = event.target.data()
        try { onEdge(JSON.parse(data.edgeDetail || '{}')) } catch { /* no-op */ }
      })
    })
    return () => { disposed = true; destroy?.() }
  }, [elements, centerId, onNode, onEdge])
  return <div ref={container} role="img" aria-label="稳健 Top10 的证据关联局部知识图谱" style={{ width: '100%', height: 'min(68vh, 700px)', minHeight: 460 }} />
}

function prismTag(value: string) {
  if (value === 'support') return <Tag color="green">ER+ 支持</Tag>
  if (value === 'anti_er_positive') return <Tag color="red">反 ER+</Tag>
  if (value === 'no_clear_direction') return <Tag>无明确方向</Tag>
  return <Tag>无记录</Tag>
}

const top20Columns: ColumnsType<Top20Row> = [
  { title: '名次', dataIndex: 'rank', width: 64, align: 'right' },
  { title: '药物', dataIndex: 'drug', render: (v: string, r) => <Space direction="vertical" size={0}>
      <Text strong>{v}</Text><Text type="secondary" style={{ fontSize: 12 }}>{r.pert_id}</Text>
    </Space> },
  { title: 'S_disc', dataIndex: 'S_disc', width: 90, align: 'right', render: (v: number) => v.toFixed(3) },
  { title: '稳定性', dataIndex: 'stability', width: 90, align: 'right',
    render: (v: number) => <Text type={v >= 0.7 ? 'success' : 'warning'}>{v.toFixed(2)}</Text> },
  { title: '剂量数', dataIndex: 'doses', width: 80, align: 'right' },
  { title: '机制链', dataIndex: 'chains', width: 80, align: 'right' },
  { title: 'PRISM', dataIndex: 'prism', width: 120, render: (v: string) => prismTag(v) },
]

const mechColumns: ColumnsType<MechRow> = [
  { title: '名次', dataIndex: 'rank', width: 64, align: 'right' },
  { title: '药物', dataIndex: 'drug', render: (v: string, r) => <Space direction="vertical" size={0}>
      <Text strong>{v}</Text><Text type="secondary" style={{ fontSize: 12 }}>{r.pert_id}</Text>
    </Space> },
  { title: 'v4 名次', dataIndex: 'rank_v4', width: 86, align: 'right' },
  { title: 'S_disc', dataIndex: 'S_disc', width: 86, align: 'right', render: (v: number) => v.toFixed(3) },
  { title: '链', dataIndex: 'chains', width: 60, align: 'right' },
  { title: 'ER+ 链', dataIndex: 'er_chains', width: 76, align: 'right' },
  { title: '链靶点', dataIndex: 'targets', render: (v: string) => <Text style={{ fontSize: 12 }}>{v}</Text> },
  { title: 'PRISM', dataIndex: 'prism', width: 120, render: (v: string) => prismTag(v) },
]

const coreColumns: ColumnsType<CoreRow> = [
  { title: '名次', dataIndex: 'rank', width: 64, align: 'right' },
  { title: '药物', dataIndex: 'drug', render: (v: string, r) => <Space direction="vertical" size={0}>
      <Text strong>{v}</Text><Text type="secondary" style={{ fontSize: 12 }}>{r.pert_id}</Text>
    </Space> },
  { title: 'v4 名次', dataIndex: 'rank_v4', width: 86, align: 'right' },
  { title: 'S_disc', dataIndex: 'S_disc', width: 86, align: 'right', render: (v: number) => v.toFixed(3) },
  { title: '机制链', dataIndex: 'chains', width: 80, align: 'right' },
  { title: 'PRISM', dataIndex: 'prism', width: 120, render: (v: string) => prismTag(v) },
]

export default function RobustResultsPage() {
  const { project } = useProject()
  const navigate = useNavigate()
  const [selectedBuildId, setSelectedBuildId] = useState<string>()
  const [selectedCandidate, setSelectedCandidate] = useState<MechRow | null>(null)
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string>()
  const [localGraphPertId, setLocalGraphPertId] = useState('all')
  const [localGraphNode, setLocalGraphNode] = useState<LocalGraphNode | null>(null)
  const [localGraphEdge, setLocalGraphEdge] = useState<LocalGraphEdge | null>(null)
  const builds = useQuery({ queryKey: ['graph-builds', project?.project_id], queryFn: () => api.graphBuilds(project!.project_id), enabled: !!project })
  const queryableBuilds = (builds.data?.items ?? []).filter(isGraphBuildQueryable)
  const activeBuildId = selectedBuildId ?? queryableBuilds[0]?.graph_build_id
  const interpretation = useMutation({ mutationFn: ({ pertId, mode }: { pertId: string; mode: 'kg_llm' | 'kg_rule' }) => api.kg07InterpretV4(project!.project_id, pertId, activeBuildId!, mode) })
  const graphEvidence = useQuery({ queryKey: ['graph-evidence', selectedEvidenceId, activeBuildId], queryFn: () => api.evidence(selectedEvidenceId!, activeBuildId), enabled: !!selectedEvidenceId })
  const { data, isLoading, isError } = useQuery({
    queryKey: ['robust-results'],
    queryFn: async () => {
      const response = await fetch('/robust-results.json')
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
      return response.json() as Promise<Payload>
    },
  })
  const localGraph = useQuery({
    queryKey: ['robust-v4-top10-local-subgraph'],
    queryFn: async () => {
      const response = await fetch('/robust-top10-subgraph.json')
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
      return response.json() as Promise<LocalGraph>
    },
    staleTime: Infinity,
  })
  const visibleLocalGraph = useMemo(() => {
    const graph = localGraph.data
    if (!graph) return { nodes: [], edges: [] }
    if (localGraphPertId === 'all') return { nodes: graph.nodes, edges: graph.edges }
    const centerId = `robust-candidate:${localGraphPertId}`
    const adjacency = new Map<string, string[]>()
    for (const edge of graph.edges) {
      adjacency.set(edge.source, [...(adjacency.get(edge.source) ?? []), edge.target])
      adjacency.set(edge.target, [...(adjacency.get(edge.target) ?? []), edge.source])
    }
    const included = new Set([centerId])
    let frontier = [centerId]
    for (let depth = 0; depth < 3; depth++) {
      const next: string[] = []
      for (const id of frontier) for (const neighbor of adjacency.get(id) ?? []) if (!included.has(neighbor)) { included.add(neighbor); next.push(neighbor) }
      frontier = next
    }
    return { nodes: graph.nodes.filter(node => included.has(node.id)), edges: graph.edges.filter(edge => included.has(edge.source) && included.has(edge.target)) }
  }, [localGraph.data, localGraphPertId])
  const localGraphElements = useMemo<ElementDefinition[]>(() => [
    ...visibleLocalGraph.nodes.map(node => ({ data: { id: node.id, label: node.label, kind: node.kind, detail: JSON.stringify(node.detail) }, classes: node.kind })),
    ...visibleLocalGraph.edges.map(edge => ({ data: { id: edge.id, source: edge.source, target: edge.target, label: edge.relation, evidenceIds: edge.evidence_ids, edgeDetail: JSON.stringify(edge) }, classes: edge.category })),
  ], [visibleLocalGraph])
  const onLocalNode = useCallback((node: LocalGraphNode) => { setLocalGraphNode(node); setLocalGraphEdge(null) }, [])
  const onLocalEdge = useCallback((edge: LocalGraphEdge) => { setLocalGraphEdge(edge); setLocalGraphNode(null) }, [])

  if (isLoading) return <Card loading />
  if (isError || !data) return <Alert type="error" showIcon message="无法读取 robust-results.json" />

  const runInterpretation = (row: MechRow, mode: 'kg_llm' | 'kg_rule') => {
    setSelectedCandidate(row)
    interpretation.reset()
    if (activeBuildId) interpretation.mutate({ pertId: row.pert_id, mode })
  }
  const goToPath = (pathId: string) => navigate(`/graph?pert_id=${encodeURIComponent(selectedCandidate?.pert_id ?? '')}&path_id=${encodeURIComponent(pathId)}&graph_build_id=${encodeURIComponent(activeBuildId ?? '')}`)
  const exportInterpretation = () => {
    if (!interpretation.data || !selectedCandidate) return
    const blob = new Blob([JSON.stringify(interpretation.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `kg07_v4_${selectedCandidate.pert_id}.json`
    anchor.click()
    URL.revokeObjectURL(url)
  }
  const interpretationSections = [
    ['筛选依据', 'screening_basis'], ['已知靶点', 'known_targets'], ['相关通路', 'associated_pathways'],
    ['独立验证', 'independent_validation'], ['机制假设', 'mechanism_hypotheses'], ['证据不足', 'insufficient_evidence'],
  ] as const
  const mechanismColumns: ColumnsType<MechRow> = [...mechColumns, {
    title: '机制解释', key: 'interpretation', width: 160,
    render: (_: unknown, row: MechRow) => <Space><Button size="small" type="primary" disabled={!activeBuildId} onClick={() => runInterpretation(row, 'kg_llm')}>AI 解释</Button><Button size="small" disabled={!activeBuildId} onClick={() => runInterpretation(row, 'kg_rule')}>规则对照</Button></Space>,
  }]

  return <Space direction="vertical" size={20} style={{ width: '100%' }}>
    <div>
      <Title level={2} style={{ marginBottom: 4 }}>最终研究结果 · 稳健候选 v4</Title>
      <Paragraph type="secondary" style={{ marginBottom: 0 }}>
        {data.protocol}　·　生成于 {new Date(data.generated_utc).toLocaleString('zh-CN')}
      </Paragraph>
    </div>

    <Alert
      type="warning"
      showIcon
      message="这是计算优先级与机制假设，不是疗效结论"
      description="外部 S1（GSE139038）与 PRISM 只作标签，不参与 v4 排序；S1 为肿瘤 vs 正常，不等同于 ER 依赖签名。"
    />

    <Card title="稳健 Top10 冻结局部知识图谱" size="small" extra={<Space wrap><Select style={{ minWidth: 230 }} value={localGraphPertId} onChange={value => { setLocalGraphPertId(value); setLocalGraphNode(null); setLocalGraphEdge(null) }} options={[{ value: 'all', label: '全部稳健 Top10' }, ...(localGraph.data?.nodes.filter(node => node.kind === 'robust-candidate').map(node => ({ value: node.detail.pert_id as string, label: `#${node.detail.rank_mech} ${node.label}` })) ?? [])]} /><Button disabled={!localGraph.data} href="/robust-top10-subgraph.json" target="_blank">下载子图 JSON</Button></Space>}>
      {project?.slug !== 'erpos-gse42568' && <Alert type="warning" showIcon message="稳健 Top10 子图属于 GSE42568 ER 阳性乳腺癌项目" />}
      {localGraph.isLoading && <Spin />}
      {localGraph.error && <Alert type="error" showIcon message="稳健 Top10 子图读取失败" description={(localGraph.error as Error).message} />}
      {localGraph.data && <>
        <Alert type={localGraph.data.status === 'PASS' ? 'info' : 'warning'} showIcon style={{ marginBottom: 12 }} message={`冻结 v4 排名 ${localGraph.data.ranking.manifest_sha256?.slice(0, 12)}… · GraphBundle ${localGraph.data.graph.analysis_run_id} · 当前视图 ${visibleLocalGraph.nodes.length} 节点 / ${visibleLocalGraph.edges.length} 条边`} description="药物映射使用精确 InChIKey；只显示 v4 方向一致、带 EvidenceRecord 的靶点边，以及有来源记录的 S1 靶点—通路富集关联。图谱关系表示证据连接，不代表因果或药效。" />
        <RobustTop10Graph elements={localGraphElements} centerId={localGraphPertId === 'all' ? undefined : `robust-candidate:${localGraphPertId}`} onNode={onLocalNode} onEdge={onLocalEdge} />
        <Space wrap style={{ marginTop: 8 }}><Tag color="blue">稳健候选</Tag><Tag color="cyan">图谱药物</Tag><Tag color="geekblue">靶点基因</Tag><Tag color="purple">S1 富集通路</Tag><Text type="secondary">映射 {localGraph.data.coverage.mapped_graph_drugs}/10 · 靶点 {localGraph.data.coverage.target_nodes} · 通路 {localGraph.data.coverage.pathway_nodes} · 证据路径 {localGraph.data.coverage.edge_count}</Text></Space>
        {localGraphNode && <Card size="small" title={`${localGraphNode.label} · ${localGraphNode.kind}`} style={{ marginTop: 12 }}><pre style={{ margin: 0, maxHeight: 220, overflow: 'auto', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(localGraphNode.detail, null, 2)}</pre></Card>}
        {localGraphEdge && <Card size="small" title={`${localGraphEdge.relation} · ${localGraphEdge.category}`} style={{ marginTop: 12 }}><Space direction="vertical" style={{ width: '100%' }}><Text>{localGraphEdge.detail.interpretation ?? localGraphEdge.detail.chain_definition ?? '精确 InChIKey 候选映射'}</Text>{localGraphEdge.evidence_ids.map(id => <CollapseEvidence key={id} id={id} evidence={localGraphEdge.evidence.find(record => record.evidence_id === id)} />)}<pre style={{ margin: 0, maxHeight: 180, overflow: 'auto', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(localGraphEdge.detail, null, 2)}</pre></Space></Card>}
        <ul style={{ marginTop: 12, marginBottom: 0, paddingLeft: 20, color: palette.muted }}>{localGraph.data.limits.map(limit => <li key={limit}>{limit}</li>)}</ul>
      </>}
    </Card>

    <Card title="筛选漏斗" size="small">
      <Row gutter={[16, 16]}>
        {data.funnel.map((item) => <Col key={item.step} xs={12} sm={8} md={6} lg={3}>
          <Statistic title={item.step} value={item.n} valueStyle={{ color: palette.ink }} />
        </Col>)}
      </Row>
    </Card>

    <Card title="数据驱动 Top20（只由 S_disc 决定）" size="small">
      <Table<Top20Row>
        rowKey="pert_id" size="small" pagination={false} columns={top20Columns} dataSource={data.top20}
      />
    </Card>

    <Card title="机制可解释 Top10（需 ≥1 条方向一致链）" size="small" extra={<Select style={{ minWidth: 320 }} value={activeBuildId} placeholder="选择可查询的 GraphBuild" options={queryableBuilds.map(build => ({ value: build.graph_build_id, label: `${build.graph_build_id} · ${build.status}` }))} onChange={setSelectedBuildId} /> }>
      {!queryableBuilds.length && <Alert type="warning" showIcon message="当前项目没有可查询的 GraphBuild，暂不能生成基于图谱证据的 AI 解释" style={{ marginBottom: 12 }} />}
      <Table<MechRow>
        rowKey="pert_id" size="small" pagination={false} columns={mechanismColumns} dataSource={data.mechanism_top10} scroll={{ x: 1100 }}
      />
    </Card>

    <Card title="高置信核心（有链且 PRISM 不反 ER+）" size="small">
      <Table<CoreRow>
        rowKey="pert_id" size="small" pagination={false} columns={coreColumns} dataSource={data.core_c}
      />
    </Card>

    <Card title="必须与结果一起读的限制" size="small">
      <ul style={{ margin: 0, paddingLeft: 20, color: palette.muted }}>
        {data.caveats.map((text) => <li key={text} style={{ marginBottom: 6 }}>{text}</li>)}
      </ul>
    </Card>
    <Modal open={!!selectedCandidate} onCancel={() => { setSelectedCandidate(null); interpretation.reset() }} width={900} title={selectedCandidate ? `${selectedCandidate.drug} · v4 机制解释` : 'v4 机制解释'} footer={null}>
      {selectedCandidate && <Space direction="vertical" style={{ width: '100%' }}>
        <Alert type="info" showIcon message={`v4 机制 Top10 第 ${selectedCandidate.rank} 名 · v4 数据排名 ${selectedCandidate.rank_v4} · S_disc ${selectedCandidate.S_disc.toFixed(3)} · GraphBuild ${activeBuildId ?? '未选择'}`} description="排序信息来自经 manifest 校验的 v4 结果；机制主张只引用所选 GraphBuild 中核验过的 Evidence ID / Path ID。模型输出仍需人工复核。" />
        <Space wrap>
          <Button type="primary" loading={interpretation.isPending} disabled={!activeBuildId} onClick={() => runInterpretation(selectedCandidate, 'kg_llm')}>生成 KG + AI 解释</Button>
          <Button loading={interpretation.isPending} disabled={!activeBuildId} onClick={() => runInterpretation(selectedCandidate, 'kg_rule')}>规则模板对照</Button>
          {interpretation.data && <Button onClick={exportInterpretation}>导出 JSON</Button>}
        </Space>
        {interpretation.isPending && <Alert type="info" showIcon message="正在按当前候选、v4 结果和 GraphBuild 证据生成解释…" />}
        {interpretation.error && <Alert type="error" showIcon message="解释生成失败" description={(interpretation.error as Error).message} />}
        {interpretation.data && <>
          <Alert type={interpretation.data.citation_reference_validation_pass ? 'success' : 'warning'} showIcon message={interpretation.data.citation_reference_validation_pass ? '保留主张的引用 ID 与当前 EvidencePackage 匹配' : '引用校验未完全通过，查看被过滤或降级的主张'} description={`模型：${interpretation.data.model ?? '规则模板'} · Prompt：${interpretation.data.prompt_version} · Evidence SHA-256：${interpretation.data.evidence_input_sha256} · v4 context SHA-256：${interpretation.data.v4_ranking_context?.context_sha256 ?? '—'} · ${interpretation.data.cached ? '命中缓存' : `耗时 ${interpretation.data.latency_seconds ?? 0}s`} · ${interpretation.data.semantic_entailment_status ?? '语义支持仍需人工审核'}`} />
          {!!interpretation.data.evidence_gaps?.length && <Alert type="warning" showIcon message="EvidencePackage 证据缺口" description={interpretation.data.evidence_gaps.join('；')} />}
          {interpretation.data.explanation?.screening_conclusion?.text && <Card size="small" title="筛选结论：为什么筛出这个药物">
            <Typography.Paragraph>{interpretation.data.explanation.screening_conclusion.text}</Typography.Paragraph>
            <Space wrap>
              {interpretation.data.explanation.screening_conclusion.path_ids?.map((id: string) => <Button size="small" key={id} onClick={() => goToPath(id)}>查看依据路径 {id.slice(0, 10)}…</Button>)}
              {interpretation.data.explanation.screening_conclusion.evidence_ids?.map((id: string) => <Button size="small" key={id} onClick={() => setSelectedEvidenceId(id)}>查看依据证据 {id.slice(0, 10)}…</Button>)}
            </Space>
          </Card>}
          {interpretation.data.explanation?.reader_summary?.text && <Card size="small" title="专业解释（证据与机制线索）">
            <Typography.Paragraph>{interpretation.data.explanation.reader_summary.text}</Typography.Paragraph>
            <Space wrap>
              {interpretation.data.explanation.reader_summary.path_ids?.map((id: string) => <Button size="small" key={id} onClick={() => goToPath(id)}>查看路径 {id.slice(0, 10)}…</Button>)}
              {interpretation.data.explanation.reader_summary.evidence_ids?.map((id: string) => <Button size="small" key={id} onClick={() => setSelectedEvidenceId(id)}>查看证据 {id.slice(0, 10)}…</Button>)}
              <Typography.Text type="secondary">引用 ID 已校验；段落语义仍需人工复核。</Typography.Text>
            </Space>
          </Card>}
          {interpretationSections.map(([label, key]) => {
            const claims = interpretation.data.explanation?.[key]
            if (!Array.isArray(claims) || !claims.length) return null
            return <Card key={key} size="small" title={label}>{claims.map((claim: Record<string, any>, index: number) => <div key={`${key}-${index}`} style={{ marginBottom: 12 }}>
              <Typography.Paragraph style={{ marginBottom: 4 }}>{claim.text}</Typography.Paragraph>
              <Space wrap>
                {claim.path_ids?.map((id: string) => <Button size="small" key={id} onClick={() => goToPath(id)}>打开路径 {id.slice(0, 10)}…</Button>)}
                {claim.evidence_ids?.map((id: string) => <Button size="small" key={id} onClick={() => setSelectedEvidenceId(id)}>证据 {id.slice(0, 10)}…</Button>)}
                {claim.relation && <Tag>{claim.relation}</Tag>}
                {claim.semantic_support_status && <Typography.Text type="secondary">语义支持需人工审核</Typography.Text>}
              </Space>
            </div>)}</Card>
          })}
          {!!interpretation.data.explanation?.limitations?.length && <Alert type="warning" showIcon message="解释限制" description={interpretation.data.explanation.limitations.join('；')} />}
          {!!interpretation.data.citation_validation_issues?.length && <Alert type="warning" showIcon message="引用核验记录" description={`${interpretation.data.citation_validation_issues.length} 条声明被删除或降级。`} />}
        </>}
      </Space>}
    </Modal>
    <Modal title="原始 EvidenceRecord" open={!!selectedEvidenceId} onCancel={() => setSelectedEvidenceId(undefined)} footer={null} width={760}>
      {graphEvidence.isLoading ? <Spin /> : graphEvidence.error ? <Alert type="error" message="证据读取失败" description={(graphEvidence.error as Error).message} /> : <pre style={{ maxHeight: 500, overflow: 'auto', whiteSpace: 'pre-wrap' }}>{JSON.stringify(graphEvidence.data, null, 2)}</pre>}
    </Modal>
  </Space>
}

function CollapseEvidence({ id, evidence }: { id: string; evidence?: Record<string, any> }) {
  return <Collapse items={[{ key: id, label: `EvidenceRecord ${id.slice(0, 12)}… · ${evidence?.source_release ?? '来源未标记'}`, children: <pre style={{ margin: 0, maxHeight: 240, overflow: 'auto', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(evidence ?? { evidence_id: id }, null, 2)}</pre> }]} />
}
