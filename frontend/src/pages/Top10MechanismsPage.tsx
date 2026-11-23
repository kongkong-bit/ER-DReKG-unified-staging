import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Alert, Button, Card, Col, Empty, Input, Modal, Row, Select, Space, Statistic, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { Core, ElementDefinition } from 'cytoscape'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../api'
import { Loading, useProject } from '../projectContext'
import { palette } from '../designTokens'

const { Title, Text } = Typography

function fmt(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  const number = Number(value)
  return Number.isFinite(number) ? number.toFixed(4) : String(value)
}

function gradeColor(grade: string) {
  return grade === 'A' ? 'green' : grade === 'B' ? 'blue' : grade === 'C' ? 'orange' : 'default'
}

type MechanismNode = { id: string; label: string; kind: string; detail: Record<string, unknown> }
type MechanismEdge = { id: string; source: string; target: string; relation: string; category: string; evidence: Record<string, unknown>; directed: boolean }

function MechanismGraph({ elements, onNode, onEdge, onReady }: { elements: ElementDefinition[]; onNode: (node: MechanismNode) => void; onEdge: (edge: MechanismEdge) => void; onReady: (graph: Core | null) => void }) {
  const host = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!host.current) return
    let disposed = false
    let graph: Core | undefined
    void import('cytoscape').then(({ default: cytoscape }) => {
      if (disposed || !host.current) return
      graph = cytoscape({
        container: host.current,
        elements,
        layout: { name: 'concentric', animate: false, fit: true, padding: 46, minNodeSpacing: 38, avoidOverlap: true, spacingFactor: 1.25, concentric: (node) => node.hasClass('candidate') ? 1000 : node.degree(), levelWidth: () => 1 },
        minZoom: 0.3,
        maxZoom: 2.8,
        style: [
          { selector: 'node', style: { label: 'data(label)', color: palette.graph.text, 'font-size': 10, 'text-wrap': 'wrap', 'text-max-width': '115px', 'text-outline-color': '#fff', 'text-outline-width': 1, width: 34, height: 34, 'background-color': palette.graph.node } },
          { selector: 'node.candidate', style: { 'background-color': palette.success, width: 54, height: 44, shape: 'round-rectangle', 'font-weight': 700 } },
          { selector: 'node.target', style: { 'background-color': '#76a9e8', shape: 'ellipse' } },
          { selector: 'node.chembl-target', style: { 'background-color': '#83b7ed', shape: 'round-rectangle' } },
          { selector: 'node.protein', style: { 'background-color': '#b7d8f5', shape: 'ellipse' } },
          { selector: 'node.pathway', style: { 'background-color': '#aa90d6', shape: 'diamond', width: 42, height: 42 } },
          { selector: 'node.drug', style: { 'background-color': '#5b9bd5', shape: 'round-rectangle' } },
          { selector: 'node.disease-evidence', style: { 'background-color': '#f0b35a', shape: 'hexagon', width: 48, height: 42 } },
          { selector: 'node.disease', style: { 'background-color': '#db8790', shape: 'round-rectangle', width: 48, height: 42 } },
          { selector: 'edge', style: { width: 2, 'line-color': palette.graph.edge, 'target-arrow-color': palette.graph.arrow, 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', label: 'data(relation)', color: palette.graph.edgeText, 'font-size': 8, 'text-background-color': '#fff', 'text-background-opacity': 0.94, 'text-background-padding': '2px' } },
          { selector: 'edge[directed = false]', style: { 'target-arrow-shape': 'none' } },
          { selector: 'edge.direct', style: { 'line-color': palette.graph.directEdge, 'target-arrow-color': palette.graph.directEdge, width: 3 } },
          { selector: 'edge.association', style: { 'line-style': 'dashed', 'line-color': palette.graph.associationEdge } },
          { selector: 'edge.chembl-mechanism', style: { 'line-style': 'dashed', 'line-color': palette.graph.mechanismEdge, 'target-arrow-color': palette.graph.mechanismEdge } },
          { selector: 'edge.chembl-component, edge.reactome-mapping', style: { 'line-color': palette.graph.pathwayEdge, 'target-arrow-color': palette.graph.pathwayEdge } },
          { selector: 'edge.s1-intersection', style: { 'line-style': 'dashed', 'line-color': palette.threshold, 'target-arrow-color': palette.threshold } },
          { selector: 'edge.expression-response', style: { 'line-style': 'dotted', 'line-color': palette.graph.expressionEdge, 'target-arrow-color': palette.graph.expressionEdge } },
          { selector: 'node:selected', style: { 'border-width': 3, 'border-color': palette.primary, 'z-index': 20 } },
        ],
      })
      onReady(graph)
      graph.on('tap', 'node', (event) => {
        const node = event.target.data()
        let detail: Record<string, unknown> = {}
        try { detail = JSON.parse(node.detail || '{}') } catch { /* preserve node details as unavailable */ }
        onNode({ id: node.id, label: node.label, kind: node.kind, detail })
      })
      graph.on('tap', 'edge', (event) => {
        const edge = event.target.data()
        let evidence: Record<string, unknown> = {}
        try { evidence = JSON.parse(edge.evidence || '{}') } catch { /* preserve source metadata as unavailable */ }
        onEdge({ id: edge.id, source: edge.source, target: edge.target, relation: edge.relation, category: edge.category, evidence, directed: edge.directed !== false })
      })
    })
    return () => { disposed = true; onReady(null); graph?.destroy() }
  }, [elements, onNode, onEdge, onReady])
  return <div ref={host} role="img" aria-label="所选候选药物的来源支持机制关系图" style={{ width: '100%', height: 'min(64vh, 620px)', minHeight: 380 }} />
}

export default function Top10MechanismsPage() {
  const { project } = useProject()
  const [selectedPertId, setSelectedPertId] = useState<string>()
  const [query, setQuery] = useState('')
  const [expressionQuery, setExpressionQuery] = useState('')
  const [expressionFilter, setExpressionFilter] = useState<'all' | 'OPPOSITE' | 'SAME' | 'NEUTRAL'>('all')
  const [graphNodeKinds, setGraphNodeKinds] = useState<string[]>([])
  const [graphRelations, setGraphRelations] = useState<string[]>([])
  const [graphEvidenceCategories, setGraphEvidenceCategories] = useState<string[]>([])
  const [selectedGraphNode, setSelectedGraphNode] = useState<MechanismNode | null>(null)
  const [selectedGraphEdge, setSelectedGraphEdge] = useState<MechanismEdge | null>(null)
  const graphInstance = useRef<Core | null>(null)
  const [targetSource, setTargetSource] = useState<'all' | 'public' | 'external'>('all')
  const [evidenceKind, setEvidenceKind] = useState<'all' | 'direct' | 'association'>('all')
  const [selectedPathwayId, setSelectedPathwayId] = useState<string>()
  const index = useQuery({ queryKey: ['top10-mechanisms-index', project?.project_id], queryFn: () => api.top10MechanismIndex(project!.project_id), enabled: !!project })
  const items = index.data?.items ?? []
  const selected = items.find((item) => item.pert_id === selectedPertId) ?? items[0]
  const graphBuilds = useQuery({ queryKey: ['top10-live-graph-builds', project?.project_id], queryFn: () => api.graphBuilds(project!.project_id), enabled: !!project })
  const liveBuildOptions = (graphBuilds.data?.items ?? []).filter((build) => build.status === 'materialized' && build.graph_source === 'neo4j')
  const [selectedGraphBuildId, setSelectedGraphBuildId] = useState<string>()
  const liveBuild = liveBuildOptions.find((build) => build.graph_build_id === selectedGraphBuildId) ?? liveBuildOptions[0]
  const livePackage = useQuery({
    queryKey: ['top10-live-kg06', project?.project_id, liveBuild?.graph_build_id, selected?.pert_id],
    queryFn: () => api.kg06Package(project!.project_id, selected!.pert_id, liveBuild!.graph_build_id),
    enabled: !!project && !!selected && !!liveBuild,
  })
  const liveRule = useQuery({
    queryKey: ['top10-live-kg07-rule', project?.project_id, liveBuild?.graph_build_id, selected?.pert_id],
    queryFn: () => api.kg07Interpret(project!.project_id, selected!.pert_id, liveBuild!.graph_build_id, 'kg_rule'),
    enabled: !!project && !!selected && !!liveBuild && !!livePackage.data,
  })
  const aiInterpretation = useMutation({
    mutationFn: (pertId: string) => api.kg07Interpret(project!.project_id, pertId, liveBuild!.graph_build_id, 'kg_llm'),
  })
  const detail = useQuery({ queryKey: ['top10-mechanism', project?.project_id, selected?.pert_id], queryFn: () => api.top10Mechanism(project!.project_id, selected!.pert_id), enabled: !!project && !!selected })
  const enrichmentReport = useQuery({ queryKey: ['top10-enrichment-report', project?.project_id, selected?.pert_id], queryFn: () => api.top10EnrichmentReport(project!.project_id, selected!.pert_id), enabled: !!project && !!selected })
  const data = detail.data
  const report = enrichmentReport.data?.report
  const pathwayNames = useMemo(() => new Map((data?.pathways ?? []).map((item) => [item.id, item.label])), [data?.pathways])
  const publicTargets = (data?.targets ?? []).map((item) => ({ key: `${item.gene.id}:${item.source}:${item.relation}`, symbol: String(item.gene.properties.symbol ?? item.gene.label), geneId: item.gene.id, relation: item.relation, source: item.source, evidence: item.evidence, external: false, kind: 'direct' as const }))
  const associations = (data?.gene_associations ?? []).map((item) => ({ key: `${item.gene.id}:${item.source}:${item.relation}`, symbol: String(item.gene.properties.symbol ?? item.gene.label), geneId: item.gene.id, relation: item.relation, source: item.source, evidence: item.evidence, external: false, kind: 'association' as const }))
  const externalTargets = (data?.external_target_evidence ?? []).map((item) => ({ key: String(item.evidence_id), symbol: item.gene_symbol, geneId: item.gene_id, relation: item.relation, source: `${item.source} · ${item.source_release}`, evidence: item, external: true, kind: 'direct' as const }))
  const chemblTargetById = new Map((data?.chembl_mechanism_targets ?? []).map((row) => [row.target_chembl_id, row]))
  const chemblRows = (data?.chembl_mechanisms ?? []).map((row) => ({ ...row, target_annotation: chemblTargetById.get(row.target_chembl_id)?.component_accession ?? '未获得蛋白组件注释' }))
  const reactomeHierarchyByChild = new Map((data?.reactome_pathway_hierarchy ?? []).map((row) => [row.child_pathway_id, row.parent_pathway_name]))
  const targetRows = [...publicTargets, ...associations, ...externalTargets].filter((row) => {
    const matchText = `${row.symbol} ${row.geneId} ${row.relation} ${row.source}`.toLowerCase().includes(query.toLowerCase())
    return matchText && (targetSource === 'all' || (targetSource === 'external' ? row.external : !row.external)) && (evidenceKind === 'all' || row.kind === evidenceKind)
  })
  const reversalRows = (data?.expression_reversal ?? []).filter((row) => {
    const text = `${row.gene_symbol} ${row.s1_gene_ids} ${row.S1_direction} ${row.S1_S2_direction_relation}`.toLowerCase()
    return text.includes(expressionQuery.toLowerCase()) && (expressionFilter === 'all' || row.S1_S2_direction_relation === expressionFilter)
  })
  const mechanismModel = useMemo(() => {
    if (!data) return { nodes: [] as MechanismNode[], edges: [] as MechanismEdge[], truncated: false }
    const nodes = new Map<string, MechanismNode>()
    const edges: MechanismEdge[] = []
    const candidateId = `candidate:${data.candidate.pert_id}`
    const addNode = (node: MechanismNode) => { if (!nodes.has(node.id)) nodes.set(node.id, node) }
    const addEdge = (edge: MechanismEdge) => { if (!edges.some((row) => row.id === edge.id)) edges.push(edge) }
    addNode({ id: candidateId, label: String(data.candidate.pert_iname), kind: 'candidate', detail: { ...data.candidate, identity: data.candidate.identity ?? data.identity_mapping } })
    for (const row of targetRows) {
      addNode({ id: row.geneId, label: row.symbol, kind: 'target', detail: { id: row.geneId, source: row.source, relation: row.relation, evidence: row.evidence } })
      addEdge({ id: `target:${row.key}`, source: candidateId, target: row.geneId, relation: row.relation, category: row.kind, evidence: { ...row.evidence, source: row.source, evidence_category: row.kind }, directed: true })
    }
    const componentRows = data.chembl_mechanism_targets
    const componentsByTarget = new Map<string, typeof componentRows>()
    for (const row of componentRows) componentsByTarget.set(row.target_chembl_id, [...(componentsByTarget.get(row.target_chembl_id) ?? []), row])
    for (const mechanism of data.chembl_mechanisms) {
      if (!mechanism.target_chembl_id) continue
      const targetId = `chembl-target:${mechanism.target_chembl_id}`
      addNode({ id: targetId, label: mechanism.target_chembl_id, kind: 'chembl-target', detail: { target_chembl_id: mechanism.target_chembl_id, mechanism_of_action: mechanism.mechanism_of_action, action_type: mechanism.action_type, source_url: `https://www.ebi.ac.uk/chembl/compound_report_card/${mechanism.molecule_chembl_id}/` } })
      const directInteraction = mechanism.direct_interaction === '1'
      addEdge({ id: `chembl-mechanism:${mechanism.mechanism_id}:${mechanism.target_chembl_id}`, source: candidateId, target: targetId, relation: directInteraction ? 'HAS_DIRECT_TARGET' : 'CHEMBL_MECHANISM_RECORD', category: directInteraction ? 'direct' : 'chembl-mechanism', evidence: { ...mechanism, source: 'ChEMBL mechanism', source_url: `https://www.ebi.ac.uk/chembl/compound_report_card/${mechanism.molecule_chembl_id}/`, interpretation: directInteraction ? 'ChEMBL 将该机制标记为直接相互作用。' : 'ChEMBL mechanism 记录，但 direct interaction 未确认；不作为直接靶点结论。' }, directed: true })
      for (const component of componentsByTarget.get(mechanism.target_chembl_id) ?? []) {
        if (!component.component_accession) continue
        const proteinId = `uniprot:${component.component_accession}`
        addNode({ id: proteinId, label: component.component_accession, kind: 'protein', detail: { ...component, source: 'ChEMBL target component' } })
        addEdge({ id: `component:${mechanism.target_chembl_id}:${component.component_accession}`, source: targetId, target: proteinId, relation: 'HAS_COMPONENT', category: 'chembl-component', evidence: { ...component, source: 'ChEMBL target component', source_url: component.source_url }, directed: true })
      }
    }
    for (const row of data.reactome_pathways) {
      if (!row.uniprot_accession || !row.pathway_id) continue
      const proteinId = `uniprot:${row.uniprot_accession}`
      const pathwayId = `pathway:${row.pathway_id}`
      addNode({ id: proteinId, label: row.uniprot_accession, kind: 'protein', detail: { uniprot_accession: row.uniprot_accession, chembl_target_name: row.chembl_target_name } })
      addNode({ id: pathwayId, label: row.pathway_name, kind: 'pathway', detail: { pathway_id: row.pathway_id, pathway_version: row.pathway_version, organism: row.organism, source_version: row.source_version, source_url: row.source_url, is_disease_pathway: row.is_disease_pathway, is_inferred: row.is_inferred } })
      addEdge({ id: `reactome:${row.uniprot_accession}:${row.pathway_id}`, source: proteinId, target: pathwayId, relation: 'PARTICIPATES_IN', category: 'reactome-mapping', evidence: { ...row, evidence_category: 'Reactome protein-component mapping' }, directed: true })
    }
    for (const route of data.pathway_routes) {
      if (!route.target_gene_id || !route.pathway_id) continue
      const geneId = String(route.target_gene_id)
      const pathwayId = `pathway:${route.pathway_id}`
      addNode({ id: geneId, label: String(route.target_symbol || geneId), kind: 'target', detail: { gene_id: geneId, source: 'S1 pathway intersection' } })
      addNode({ id: pathwayId, label: pathwayNames.get(route.pathway_id) ?? route.pathway_id, kind: 'pathway', detail: { pathway_id: route.pathway_id, pathway_name: pathwayNames.get(route.pathway_id) ?? route.pathway_id, evidence_scope: 'S1 pathway intersection only' } })
      addEdge({ id: `s1-route:${geneId}:${route.pathway_id}`, source: geneId, target: pathwayId, relation: 'S1_PATHWAY_INTERSECTION', category: 's1-intersection', evidence: { ...route, interpretation: '基于靶点与 S1 富集基因/通路成员的交集；不表示直接调控或通路参与。' }, directed: false })
    }
    for (const response of data.expression_evidence) {
      if (!response.target_gene_id) continue
      const geneId = String(response.target_gene_id)
      addNode({ id: geneId, label: String(response.target_symbol || geneId), kind: 'target', detail: { ...response, evidence_scope: 'S1/S2 target expression response' } })
      addEdge({ id: `expression:${geneId}:${response.sig_id}`, source: candidateId, target: geneId, relation: 'S2_TRANSCRIPTIONAL_RESPONSE', category: 'expression-response', evidence: { ...response, source: 'LINCS Level 5 GCTX', interpretation: '转录响应值，不是直接结合、靶点活性或疗效测量。' }, directed: true })
    }
    const diseaseGraph = data.disease_evidence_graph
    const graphNodes = new Map(diseaseGraph.nodes.map((node) => [node.id, node]))
    const graphDrug = diseaseGraph.nodes.find((node) => node.type === 'Drug')
    for (const node of diseaseGraph.nodes) {
      const kind = node.type === 'DiseaseEvidence' ? 'disease-evidence' : node.type === 'Disease' ? 'disease' : 'drug'
      addNode({ id: node.id, label: node.label, kind, detail: { ...node.properties, id: node.id, source_node_type: node.type } })
    }
    if (graphDrug) {
      addEdge({ id: `disease-evidence:identity:${graphDrug.id}`, source: candidateId, target: graphDrug.id, relation: 'REFERENCES_DRUG', category: 'disease-context', evidence: { mapping: data.identity_mapping, interpretation: '候选由冻结 LINCS 身份精确映射到标准药物实体。' }, directed: true })
    }
    for (const edge of diseaseGraph.edges) {
      const source = edge.from === diseaseGraph.candidate_node_id ? candidateId : edge.from
      if (!graphNodes.has(edge.to) || (source !== candidateId && !graphNodes.has(source))) continue
      const claimNode = graphNodes.get(edge.from)?.type === 'DiseaseEvidence' ? graphNodes.get(edge.from) : graphNodes.get(edge.to)
      addEdge({ id: `disease-evidence:${edge.label}:${edge.from}:${edge.to}`, source, target: edge.to, relation: edge.label, category: 'disease-context', evidence: { ...edge.properties, source: edge.source_release, source_url: claimNode?.properties.source_url, source_id: claimNode?.properties.source_id, context: claimNode?.properties.context, limitations: claimNode?.properties.limitations, interpretation: '人工审查的疾病背景证据路径；描述研究上下文，不表示该药物治疗该疾病。' }, directed: true })
    }
    const maxEdges = 120
    const diseaseContextEdges = edges.filter((edge) => edge.category === 'disease-context')
    const otherEdges = edges.filter((edge) => edge.category !== 'disease-context')
    const visibleEdges = [...diseaseContextEdges, ...otherEdges.slice(0, Math.max(0, maxEdges - diseaseContextEdges.length))]
    return { nodes: [...nodes.values()], edges: visibleEdges, truncated: visibleEdges.length < edges.length }
  }, [data, targetRows, pathwayNames])
  const graphNodeTypeOptions = useMemo(() => [...new Set(mechanismModel.nodes.map((node) => node.kind))].map((value) => ({ value, label: ({ candidate: '候选药物', drug: '标准药物实体', target: '靶点 / 基因', protein: '蛋白', 'chembl-target': 'ChEMBL 靶点实体', pathway: '通路', 'disease-evidence': '疾病证据', disease: '疾病' } as Record<string, string>)[value] ?? value })), [mechanismModel.nodes])
  const graphRelationOptions = useMemo(() => [...new Set(mechanismModel.edges.map((edge) => edge.relation))].map((value) => ({ value, label: value })), [mechanismModel.edges])
  const graphEvidenceOptions = useMemo(() => [...new Set(mechanismModel.edges.map((edge) => edge.category))].map((value) => ({ value, label: ({ direct: '来源支持直接作用', association: '一般药物—基因关联', 'chembl-mechanism': 'ChEMBL 机制记录', 'chembl-component': '靶点组件', 'reactome-mapping': 'Reactome 参与映射', 's1-intersection': 'S1 通路交集', 'expression-response': 'S2 表达响应', 'disease-context': '人工疾病背景证据' } as Record<string, string>)[value] ?? value })), [mechanismModel.edges])
  const visibleGraph = useMemo(() => {
    const nodeKinds = new Set(graphNodeKinds)
    const relations = new Set(graphRelations)
    const categories = new Set(graphEvidenceCategories)
    const visibleNodes = mechanismModel.nodes.filter((node) => nodeKinds.size === 0 || nodeKinds.has(node.kind))
    const nodeIds = new Set(visibleNodes.map((node) => node.id))
    const visibleEdges = mechanismModel.edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target) && (relations.size === 0 || relations.has(edge.relation)) && (categories.size === 0 || categories.has(edge.category)) && (!selectedPathwayId || !edge.target.startsWith('pathway:') || edge.target === `pathway:${selectedPathwayId}`))
    const connected = new Set(visibleEdges.flatMap((edge) => [edge.source, edge.target]))
    const retainedNodes = visibleNodes.filter((node) => node.kind === 'candidate' || connected.has(node.id))
    return [
      ...retainedNodes.map((node) => ({ data: { id: node.id, label: node.label, kind: node.kind, detail: JSON.stringify(node.detail) }, classes: node.kind })),
      ...visibleEdges.map((edge) => ({ data: { id: edge.id, source: edge.source, target: edge.target, relation: edge.relation, category: edge.category, evidence: JSON.stringify(edge.evidence), directed: edge.directed }, classes: edge.category })),
    ] as ElementDefinition[]
  }, [mechanismModel, graphNodeKinds, graphRelations, graphEvidenceCategories, selectedPathwayId])
  const onGraphNode = useCallback((node: MechanismNode) => setSelectedGraphNode(node), [])
  const onGraphEdge = useCallback((edge: MechanismEdge) => setSelectedGraphEdge(edge), [])
  const onGraphReady = useCallback((graph: Core | null) => { graphInstance.current = graph }, [])
  const targetColumns: ColumnsType<(typeof targetRows)[number]> = [
    { title: '靶点/关联基因', dataIndex: 'symbol', key: 'symbol', render: (value, row) => <Space direction="vertical" size={0}><Text strong>{value}</Text><Text type="secondary" code>{row.geneId}</Text></Space> },
    { title: '证据类别', dataIndex: 'kind', key: 'kind', render: (value) => <Tag color={value === 'direct' ? 'blue' : 'default'}>{value === 'direct' ? '直接作用证据' : '药物—基因关联'}</Tag> },
    { title: '作用/关系', dataIndex: 'relation', key: 'relation', render: (value) => <Tag color="blue">{value}</Tag> },
    { title: '来源', dataIndex: 'source', key: 'source' },
    { title: '证据记录', key: 'evidence', render: (_, row) => {
      const props = row.evidence as Record<string, any>
      const url = props.source_url
      const record = props.source_record_id ?? props.source_record ?? props.source_ids?.join(', ')
      return <Space direction="vertical" size={0}>{url ? <a href={url} target="_blank" rel="noreferrer">查看来源</a> : <Text type="secondary">来源记录</Text>}<Text type="secondary">{record || props.source_release || '—'}</Text></Space>
    } },
  ]
  const chemblColumns: ColumnsType<Record<string, string>> = [
    { title: 'ChEMBL 整理的作用机制', dataIndex: 'mechanism_of_action', key: 'mechanism', width: 280 },
    { title: '靶点 / 组件 accession', key: 'target', render: (_, row) => <Space direction="vertical" size={0}><Text>{row.target_chembl_id || '靶点未指定'}</Text><Text type="secondary">{row.target_annotation}</Text></Space> },
    { title: '方向及直接性标记', key: 'action', render: (_, row) => <Space wrap><Tag color="blue">{row.action_type || '方向未标注'}</Tag><Tag>{row.direct_interaction === '1' ? 'ChEMBL 标记 direct' : 'direct 未确认'}</Tag></Space> },
    { title: '记录与来源', key: 'source', render: (_, row) => { let refs: Array<{ref_id?:string;ref_url?:string}> = []; try { refs = JSON.parse(row.mechanism_refs || '[]') } catch { /* malformed source metadata stays visible as unavailable */ } return <Space direction="vertical" size={0}><a href={`https://www.ebi.ac.uk/chembl/compound_report_card/${row.molecule_chembl_id}/`} target="_blank" rel="noreferrer">ChEMBL {row.molecule_chembl_id}</a><Text type="secondary">{refs.map((ref) => ref.ref_id).filter(Boolean).join(', ') || '未返回 PMID'}</Text></Space> } },
  ]
  const dgidbColumns: ColumnsType<Record<string, string>> = [
    { title: '基因', dataIndex: 'gene_name', key: 'gene', render: (value, row) => <Space direction="vertical" size={0}><Text strong>{value}</Text><Text type="secondary">{row.gene_concept_id}</Text></Space> },
    { title: '互动类型', dataIndex: 'interaction_types', key: 'types', render: (value) => value || '未标注' },
    { title: '来源库 / PubMed', key: 'source', render: (_, row) => <Space direction="vertical" size={0}><Text>{row.sources || '来源库未列出'}</Text><Text type="secondary">{row.publications || '未返回 PMID'}</Text></Space> },
    { title: '证据分数', dataIndex: 'interaction_score', key: 'score', render: fmt },
    { title: '解释限制', dataIndex: 'interpretation', key: 'limit' },
  ]
  const routeColumns: ColumnsType<Record<string, string>> = [
    { title: '靶点基因', dataIndex: 'target_gene_id', key: 'target_gene_id', render: (value) => <Text code>{value}</Text> },
    { title: 'S1 富集通路', dataIndex: 'pathway_id', key: 'pathway_id', render: (value) => <Space direction="vertical" size={0}><Text>{pathwayNames.get(value) ?? value}</Text><Text type="secondary" code>{value}</Text></Space> },
    { title: '关系解释', dataIndex: 'interpretation', key: 'interpretation' },
  ]
  const reactomeColumns: ColumnsType<Record<string, string>> = [
    { title: 'ChEMBL 靶点组件', key: 'component', render: (_, row) => <Space direction="vertical" size={0}><Text>{row.chembl_target_name}</Text><Tag>{row.chembl_target_type}</Tag><Text type="secondary" code>{row.uniprot_accession}</Text></Space> },
    { title: 'Reactome 通路', key: 'pathway', render: (_, row) => <Space direction="vertical" size={0}><a href={row.source_url} target="_blank" rel="noreferrer">{row.pathway_name}</a><Text type="secondary" code>{row.pathway_id} · v{row.pathway_version}</Text></Space> },
    { title: '层级 / 注释', key: 'hierarchy', render: (_, row) => <Space direction="vertical" size={0}><Text>父通路：{reactomeHierarchyByChild.get(row.pathway_id) ?? '未返回父级'}</Text><Space><Tag color={row.is_disease_pathway === 'True' ? 'orange' : 'default'}>{row.is_disease_pathway === 'True' ? 'Reactome disease pathway' : '非疾病通路'}</Tag>{row.is_inferred === 'True' && <Tag>inferred</Tag>}</Space></Space> },
  ]
  const regulatoryPathColumns: ColumnsType<Record<string, any>> = [
    { title: 'S1 终端基因', key: 'terminal', render: (_, row) => <Space direction="vertical" size={0}><Text strong>{row.terminal_gene || '未映射'}</Text><Text type="secondary" code>{row.terminal_gene_node_id || '—'}</Text><Text>S1 {row.terminal_s1_direction || 'unknown'} · logFC {fmt(row.terminal_s1_logFC)}</Text></Space> },
    { title: '调控符号', dataIndex: 'direction', key: 'direction', render: (value) => <Tag color={value === 'positive' ? 'green' : value === 'negative' ? 'volcano' : 'orange'}>{value || 'unknown'}</Tag> },
    { title: '调控步数 / 上下文', key: 'context', render: (_, row) => <Space direction="vertical" size={0}><Text>{row.edge_ids?.length ?? 0} 步</Text><Text type="secondary">{row.cell_context || 'unknown'}{row.context_compatible === false ? ' · context conflict' : ''}</Text></Space> },
    { title: '来源与文献证据', key: 'evidence', render: (_, row) => { const evidence = (row.evidence ?? []) as Array<Record<string, any>>; const refs = [...new Set(evidence.flatMap((item) => String(item.evidence_ids ?? '').split(/[|;]/).filter((ref) => ref.startsWith('PMID:'))))]; return <Space direction="vertical" size={0}>{refs.length ? <Text>{refs.map((ref) => { const pmid = ref.slice(5); return <a key={ref} href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}/`} target="_blank" rel="noreferrer">PMID {pmid} · </a> })}</Text> : <Text type="secondary">无 PMID</Text>}<Text type="secondary">{evidence.map((item) => `${item.source_release ?? ''} ${item.source_record_id ?? ''}`).filter(Boolean).join(' · ') || (row.edge_ids ?? []).join(', ')}</Text><Text type="secondary">Path evidence: {(row.evidence_ids ?? []).length}</Text></Space> } },
    { title: 'S2 终端响应', key: 's2', render: (_, row) => <Text>{(row.s2_terminal_response ?? []).length ? (row.s2_terminal_response as Array<Record<string, any>>).map((item) => `COMPZ ${fmt(item.COMPZ)}`).join(' · ') : '无可比的终端基因响应记录'}</Text> },
  ]
  const contextPathColumns: ColumnsType<Record<string, any>> = [
    { title: '上下文路线', key: 'route', render: (_, row) => <Text>{(row.nodes ?? []).join(' → ')}</Text> },
    { title: '解释边界', dataIndex: 'interpretation', key: 'interpretation' },
    { title: '证据记录', key: 'evidence', render: (_, row) => <Text type="secondary">{(row.evidence ?? []).map((item: Record<string, any>) => item.source_record_id).filter(Boolean).join(' · ') || (row.evidence_ids ?? []).join(', ')}</Text> },
  ]
  const expressionColumns: ColumnsType<Record<string, string>> = [
    { title: '靶点', dataIndex: 'target_symbol', key: 'target_symbol' },
    { title: 'S1 疾病方向', dataIndex: 'S1_direction', key: 'S1_direction', render: (value) => value ? <Tag color={value === 'UP' ? 'red' : 'blue'}>{value}</Tag> : '无显著方向' },
    { title: 'S1 logFC / FDR', key: 's1', render: (_, row) => `${fmt(row.S1_logFC)} / ${fmt(row.S1_FDR)}` },
    { title: 'S2 LINCS COMPZ', dataIndex: 'COMPZ', key: 'COMPZ', render: fmt },
    { title: '方向关系', dataIndex: 'S2_S1_relation', key: 'S2_S1_relation' },
  ]
  const diseaseColumns: ColumnsType<Record<string, string>> = [
    { title: '证据范围', dataIndex: 'evidence_scope', key: 'scope', render: (value) => <Tag color={value === 'ER_positive_preclinical' ? 'green' : 'default'}>{value}</Tag> },
    { title: '研究背景', dataIndex: 'context', key: 'context' },
    { title: '整理结果', dataIndex: 'curated_finding', key: 'finding' },
    { title: '方向', dataIndex: 'direction', key: 'direction', render: (value) => <Tag color={value === 'supportive_preclinical' ? 'green' : value === 'counter_or_mixed' ? 'orange' : 'default'}>{value}</Tag> },
    { title: '来源', key: 'source', render: (_, row) => <Space direction="vertical" size={0}><a href={row.source_url} target="_blank" rel="noreferrer">{row.source_id}</a><Text type="secondary">{row.source_type}</Text></Space> },
    { title: '限制', dataIndex: 'limitations', key: 'limitations' },
  ]
  const reversalColumns: ColumnsType<Record<string, string>> = [
    { title: '基因', dataIndex: 'gene_symbol', key: 'gene_symbol', render: (value, row) => <Space direction="vertical" size={0}><Text strong>{value}</Text><Text type="secondary" code>{row.s1_gene_ids || row.lincs_gene_id}</Text></Space> },
    { title: 'S1 方向', dataIndex: 'S1_direction', key: 'S1_direction', render: (value) => <Tag color={value === 'UP' ? 'red' : 'blue'}>{value}</Tag> },
    { title: 'S1 logFC / FDR', key: 's1-stat', render: (_, row) => `${fmt(row.S1_logFC)} / ${fmt(row.S1_FDR)}` },
    { title: '冻结签名 S2 COMPZ', dataIndex: 'S2_COMPZ_median', key: 'S2_COMPZ_median', render: fmt },
    { title: '方向交叉', dataIndex: 'S1_S2_direction_relation', key: 'S1_S2_direction_relation', render: (value) => <Tag color={value === 'OPPOSITE' ? 'green' : value === 'SAME' ? 'orange' : 'default'}>{value}</Tag> },
  ]
  const robustnessColumns: ColumnsType<Record<string, string>> = [
    { title: '复核', dataIndex: 'study', key: 'study', fixed: 'left', width: 110 },
    { title: '指标', dataIndex: 'metric', key: 'metric', width: 190 },
    { title: '结果', dataIndex: 'value', key: 'value', render: (value) => value || '—' },
    { title: '范围与限制', dataIndex: 'limit', key: 'limit', width: 320 },
  ]
  const robustness = data?.robustness_evidence?.[0]
  const robustnessRows: Record<string, string>[] = robustness ? [
    { key: 'exp006_dose', study: 'Exp006', metric: '24 h 合格剂量；WTCS 负向比例', value: `${robustness.exp006_dose_count || '—'}；${robustness.exp006_negative_dose_fraction ? `${fmt(Number(robustness.exp006_negative_dose_fraction) * 100)}%` : '—'}`, limit: robustness.exp006_limitations || '历史剂量敏感性结果' },
    { key: 'exp006_stability', study: 'Exp006', metric: '剂量稳定等级 / QC 范围', value: `${robustness.exp006_dose_stability || '—'} / ${robustness.exp006_qc_sensitivity_range || '—'} (${robustness.exp006_stability_grade || '—'})`, limit: '历史分析；单条主条件签名不能视为独立重复' },
    { key: 'exp007', study: 'Exp007', metric: 'A / B100 / B150 / B200 / B300 / 匹配基因集排名', value: [robustness.exp007_rank_A_original, robustness.exp007_rank_B100, robustness.exp007_rank_B150, robustness.exp007_rank_B200, robustness.exp007_rank_B300, robustness.exp007_rank_B_matched125].map((x) => x || '—').join(' / '), limit: '不同签名基因集方案下的历史候选排名；不改变正式冻结排名' },
    { key: 'exp008', study: 'Exp008', metric: '历史 B200 置换经验 P / BH FDR', value: `${robustness.exp008_empirical_pvalue_B200_historical || '—'} / ${robustness.exp008_BH_FDR_B200_historical || '—'}`, limit: robustness.exp008_scope || '历史置换统计；未在本轮更正后的签名集合重算' },
    { key: 'exp009', study: 'Exp009', metric: '质量阈值排名敏感性', value: robustness.exp009_status === 'available' ? `CC≥0.2: ${robustness.exp009_rank_CC02 || '—'}；CC≥0.1: ${robustness.exp009_rank_CC01 || '—'}；CC≥0.3: ${robustness.exp009_rank_CC03 || '—'}；CC≥0.2/TAS≥0.2: ${robustness.exp009_rank_CC02_TAS02 || '—'}` : robustness.exp009_status, limit: '未列入该实验结果表示不可用/未匹配，不代表负结果' },
    { key: 'exp010', study: 'Exp010', metric: '独立 ER+ 队列 S1 的 WTCS / 名次', value: robustness.exp010_status === 'available' ? `${robustness.exp010_external_S1_WTCS || '—'} / ${robustness.exp010_external_S1_rank || '—'}` : robustness.exp010_status, limit: '独立表达队列复核；覆盖不全，头部名单可变化' },
    { key: 'exp011', study: 'Exp011', metric: 'PRISM ER+ / ER− 平均敏感性；细胞系数', value: robustness.exp011_status === 'available' ? `${robustness.exp011_ERpos_mean_sensitivity || '—'} / ${robustness.exp011_ERneg_mean_sensitivity || '—'}；${robustness.exp011_ERpos_cell_lines || '—'} / ${robustness.exp011_ERneg_cell_lines || '—'}` : robustness.exp011_status, limit: '细胞存活敏感性是不同于 LINCS WTCS 的终点，不能解读为疗效概率' },
  ] : []
  const exportReport = () => {
    if (!data) return
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${data.candidate.pert_id}_mechanism.json`
    anchor.click()
    URL.revokeObjectURL(url)
  }
  if (index.isLoading) return <Loading />
  if (index.error) return <Loading error={index.error as Error} />
  if (!items.length) return <Empty description="当前项目没有可用的 Top 10 专项机制证据" />
  return <Space direction="vertical" size="large" style={{ width: '100%' }}>
    <div className="page-heading"><div><Text className="eyebrow">历史冻结结果 / WTCS M0 基线</Text><Title level={2}>冻结 WTCS Top 10 机制档案</Title><Text type="secondary">这是旧版单算法正式榜单的审计入口。当前稳健机制 Top10 按 v4 新规则生成，请前往 <a href="/top10-mechanisms">稳健候选 Top10 · v4</a>。</Text></div><Button onClick={exportReport} disabled={!data}>导出当前药物证据 JSON</Button></div>
    <Alert type="warning" showIcon message="本页专题档案来自已校验离线图包" description="该离线包尚未登记为 GraphBuild，也未导入 Neo4j。下方“实时 GraphBuild”卡片会单独读取当前已导入版本的 KG06/KG07 结果。两种来源中的路径都表示证据关系交汇，不证明因果、靶点占有、治疗效果或 ER+ 特异性。" />
    <Row gutter={[16, 16]}>
      <Col xs={12} md={6}><Card><Statistic title="正式候选" value={items.length} suffix="种" /></Card></Col>
      <Col xs={12} md={6}><Card><Statistic title="精确身份映射" value={items.filter((item) => item.identity_status.startsWith('matched')).length} suffix={`/ ${items.length}`} /></Card></Col>
      <Col xs={12} md={6}><Card><Statistic title="有靶点证据" value={items.filter((item) => item.direct_target_assertion_count > 0).length} suffix={`/ ${items.length}`} /></Card></Col>
      <Col xs={12} md={6}><Card><Statistic title="机制证据等级 A / B / C / U" value={['A', 'B', 'C', 'U'].map((grade) => items.filter((item) => item.mechanism_evidence_grade === grade).length).join(' / ')} /></Card></Col>
    </Row>
    <Card title="选择候选药物" className="section-card">
      <Select aria-label="选择 Top 10 候选药物" style={{ width: 'min(100%, 560px)' }} value={selected?.pert_id} options={items.map((item) => ({ value: item.pert_id, label: `#${item.rank} ${item.pert_iname} · WTCS ${fmt(item.wtcs)} · ${item.mechanism_evidence_grade}级` }))} onChange={setSelectedPertId} />
      {selected && <div style={{ marginTop: 16 }}><Space wrap><Tag color="purple">排名 #{selected.rank}</Tag><Tag color={selected.identity_status.startsWith('matched') ? 'green' : 'orange'}>{selected.identity_status}</Tag><Tag color={gradeColor(selected.mechanism_evidence_grade)}>机制证据 {selected.mechanism_evidence_grade}级 · {selected.mechanism_evidence_grade_label}</Tag><Text code>{selected.pert_id}</Text><Text>WTCS {fmt(selected.wtcs)}</Text><Text type="secondary">{selected.sig_id}</Text></Space></div>}
    </Card>
    <Card title="实时 GraphBuild · KG06 Evidence Package · KG07 规则解释" className="section-card">
      {graphBuilds.isLoading ? <Loading /> : graphBuilds.error ? <Alert type="error" showIcon message="图谱版本列表读取失败" description={(graphBuilds.error as Error).message} /> : liveBuildOptions.length ? <Space direction="vertical" style={{ width: '100%' }}>
        <Space wrap><Text>选择已导入的 Neo4j 图谱版本</Text><Select aria-label="选择实时 Neo4j GraphBuild" style={{ width: 'min(100%, 760px)' }} value={liveBuild?.graph_build_id} options={liveBuildOptions.map((build) => ({ value: build.graph_build_id, label: `${build.graph_build_id} · ${String(build.summary.node_count ?? '—')} 节点 / ${String(build.summary.edge_count ?? '—')} 边` }))} onChange={setSelectedGraphBuildId} /></Space>
        {livePackage.isLoading ? <Loading /> : livePackage.error ? <Alert type="warning" showIcon message="该候选在所选 GraphBuild 中没有可用的 KG06 包" description={(livePackage.error as Error).message} /> : livePackage.data && <>
          <Alert type={livePackage.data.coverage?.evidence_integrity_pass ? 'success' : 'warning'} showIcon message={`KG06 ${livePackage.data.package_id}`} description={`GraphBuild ${livePackage.data.graph_build_id} · ${livePackage.data.paths?.length ?? 0} 条路径 · ${livePackage.data.coverage?.unique_evidence_count ?? 0} 条独立证据 · ${livePackage.data.coverage?.s2_condition_count ?? 0} 条 S2 条件；完整性 ${livePackage.data.coverage?.evidence_integrity_pass ? '通过' : '需检查'}。`} />
          {!!livePackage.data.evidence_gaps?.length && <Alert type="warning" showIcon message="当前候选的证据缺口" description={<ul style={{ marginBottom: 0 }}>{livePackage.data.evidence_gaps.map((gap: string) => <li key={gap}>{gap}</li>)}</ul>} />}
          <Table size="small" rowKey="path_id" pagination={{ pageSize: 5, showSizeChanger: false }} dataSource={(livePackage.data.paths ?? []).slice(0, 20)} columns={[
            { title: '证据路径', dataIndex: 'route_type', key: 'route_type' },
            { title: '靶点', dataIndex: 'target_gene_id', key: 'target_gene_id', render: (value: string) => value || '—' },
            { title: '通路', dataIndex: 'pathway_label', key: 'pathway_label', render: (value: string) => value || '—' },
            { title: '可核查证据 ID', key: 'evidence_ids', render: (_: unknown, row: Record<string, any>) => <Text code>{(row.evidence_ids ?? []).length ? `${row.evidence_ids.length} · ${(row.evidence_ids as string[]).slice(0, 2).join(', ')}` : '—'}</Text> },
          ]} locale={{ emptyText: '此候选在该 GraphBuild 中没有完整机制路径；证据缺口已保留。' }} />
          {liveRule.isLoading ? <Loading /> : liveRule.error ? <Alert type="error" showIcon message="KG07 规则解释读取失败" description={(liveRule.error as Error).message} /> : liveRule.data && <>
            <Alert type={liveRule.data.citation_reference_validation_pass ? 'success' : 'warning'} showIcon message={`KG07 ${liveRule.data.status} · 引用校验 ${liveRule.data.citation_reference_validation_pass ? '通过' : '未通过'} · 人工复核：${liveRule.data.human_review_required ? '需要' : '未标记'}`} description={`候选 ${liveRule.data.candidate?.drug_name ?? selected?.pert_iname} · ${(liveRule.data.evidence_gaps ?? []).length ? `证据缺口 ${(liveRule.data.evidence_gaps as string[]).join('；')}` : '规则层未发现额外证据缺口'}；这是规则模板，不是 GLM 生成结果。`} />
            <Space direction="vertical" style={{ width: '100%' }}>{Object.entries(liveRule.data.explanation ?? {}).flatMap(([section, claims]) => Array.isArray(claims) ? claims.map((claim: Record<string, any>, index: number) => ({ section, claim, index })) : []).map(({ section, claim, index }) => <Card size="small" key={`${section}:${index}`} title={section}><Text>{claim.text}</Text><div style={{ marginTop: 6 }}><Text type="secondary">引用：{[...(claim.evidence_ids ?? []), ...(claim.path_ids ?? [])].slice(0, 4).join(' · ') || '没有引用标识'}</Text></div></Card>)}</Space>
            <div style={{ marginTop: 16 }}>
              <Button type="primary" loading={aiInterpretation.isPending} onClick={() => selected && aiInterpretation.mutate(selected.pert_id)} disabled={!selected || !liveBuild}>使用 GLM-5.3-Flash 生成 AI 机制解释</Button>
              {aiInterpretation.error && <Alert type="error" showIcon style={{ marginTop: 12 }} message="AI 机制解释失败" description={(aiInterpretation.error as Error).message} />}
              {aiInterpretation.data && aiInterpretation.variables === selected?.pert_id && <div style={{ marginTop: 12 }}>
                <Alert type={aiInterpretation.data.citation_validation_pass ? 'success' : 'warning'} showIcon message={`${aiInterpretation.data.model ?? 'GLM'} AI 解释${aiInterpretation.data.cached ? '（缓存）' : ''} · 引用校验 ${aiInterpretation.data.citation_validation_pass ? '通过' : '部分未通过'}`} description={aiInterpretation.data.citation_validation_pass ? '保留的结论通过 Evidence ID / Path ID 校验；仍需人工审核机制语义。' : `存在 ${aiInterpretation.data.citation_validation_issues?.length ?? 0} 条引用或结构问题，未验证的断言已由后端过滤。保留引用可核验：${aiInterpretation.data.citation_reference_validation_pass ? '通过' : '未通过'}。`} />
                <Space direction="vertical" style={{ width: '100%', marginTop: 12 }}>{Object.entries(aiInterpretation.data.explanation ?? {}).flatMap(([section, claims]) => Array.isArray(claims) ? claims.map((claim: Record<string, any>, index: number) => ({ section, claim, index })) : []).map(({ section, claim, index }) => <Card size="small" key={`ai:${section}:${index}`} title={section}><Text>{claim.text}</Text><div style={{ marginTop: 6 }}><Text type="secondary">证据引用：{[...(claim.evidence_ids ?? []), ...(claim.path_ids ?? [])].slice(0, 6).join(' · ') || '没有可验证的引用 ID'}{claim.semantic_support_status ? ` · ${claim.semantic_support_status}` : ''}</Text></div></Card>)}</Space>
              </div>}
            </div>
          </>}
        </>}
      </Space> : <Alert type="info" showIcon message="当前项目没有已导入 Neo4j 的 GraphBuild" description="离线专项图包仍可浏览；导入 GraphBundle 并创建 materialized GraphBuild 后，此处会按所选候选读取 KG06/KG07。" />}
    </Card>
    {detail.isLoading ? <Loading /> : detail.error ? <Alert type="error" showIcon message="机制证据读取失败" description={(detail.error as Error).message} /> : data && <>
      {data.identity_mapping && <Card title="身份映射"><DescriptionsLike values={data.identity_mapping} /></Card>}
      <Alert type={data.mechanism_evidence_grade.grade === 'A' ? 'success' : data.mechanism_evidence_grade.grade === 'C' || data.mechanism_evidence_grade.grade === 'U' ? 'warning' : 'info'} showIcon message={`机制证据等级 ${data.mechanism_evidence_grade.grade} · ${data.mechanism_evidence_grade.grade_label}`} description={<Space direction="vertical"><Text>{data.mechanism_evidence_grade.grade_rationale}</Text><Text>{data.mechanism_evidence_grade.limitations}</Text><Text type="secondary">这是按当前靶点药理与疾病背景材料人工审阅的机制证据等级，不是药物疗效概率；定向检索不等于系统综述。</Text><Text>疾病来源：{data.mechanism_evidence_grade.disease_source_id || '未提供'}{data.mechanism_evidence_grade.disease_source_url ? <> · <a href={data.mechanism_evidence_grade.disease_source_url} target="_blank" rel="noreferrer">查看记录</a></> : null}</Text>{data.mechanism_evidence_grade.mechanism_source_refs && <Text>ChEMBL 机制 PMID：{data.mechanism_evidence_grade.mechanism_source_refs.split(';').map((pmid) => pmid.trim()).filter(Boolean).map((pmid) => <span key={pmid}> · <a href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}/`} target="_blank" rel="noreferrer">{pmid}</a></span>)}</Text>}{data.mechanism_evidence_grade.target_source_urls && <Text>直接靶点来源：{data.mechanism_evidence_grade.target_source_urls.split(';').map((url) => url.trim()).filter(Boolean).map((url) => <span key={url}> · <a href={url} target="_blank" rel="noreferrer">查看来源</a></span>)}</Text>}{data.mechanism_evidence_grade.target_source_records && <Text type="secondary">原始靶点记录：{data.mechanism_evidence_grade.target_source_records}</Text>}{data.mechanism_evidence_grade.target_evidence_ids && <Text type="secondary">靶点 Evidence ID：{data.mechanism_evidence_grade.target_evidence_ids}</Text>}</Space>} />
      {enrichmentReport.isLoading ? <Loading /> : enrichmentReport.error ? <Alert type="error" showIcon message="增强机制评估报告不可用" description={(enrichmentReport.error as Error).message} /> : report && <Card title="增强机制评估与证据缺口" className="section-card">
        <Alert type={report.candidate_mechanism_paths.length ? 'info' : 'warning'} showIcon message={report.candidate_mechanism_paths.length ? `已找到 ${report.candidate_mechanism_paths.length} 条有向调控候选路径` : '当前没有连接到 S1 基因的有向调控路径'} description={report.interpretation} style={{ marginBottom: 12 }} />
        <Row gutter={[12, 12]}>
          {Object.entries(report.rule_based_dimensions).filter(([key]) => key !== 'ranking_policy').map(([key, dimension]) => <Col xs={24} md={12} xl={8} key={key}>
            <Card size="small" title={key}>
              <Space direction="vertical" size={4}><Tag color={dimension.missing ? 'default' : 'blue'}>{String(dimension.value ?? '未评估')}</Tag><Text type="secondary">{String(dimension.basis ?? dimension.record_count ?? dimension.wtcs ?? '')}</Text></Space>
            </Card>
          </Col>)}
        </Row>
        {report.candidate_mechanism_paths.length > 0 && <><Title level={5} style={{ marginTop: 18 }}>有向调控路径与逐路径证据</Title><Table size="small" rowKey={(row) => (row.edge_ids ?? []).join('|')} dataSource={report.candidate_mechanism_paths} columns={regulatoryPathColumns} pagination={{ pageSize: 8, showSizeChanger: false }} scroll={{ x: 900 }} /><Text type="secondary">路径符号描述调控边效应；S1 mRNA 方向没有被当作蛋白活性。打开 PMID 和来源记录核查实验背景。</Text></>}
        {report.candidate_context_paths.length > 0 && <><Title level={5} style={{ marginTop: 18 }}>非因果药物—通路上下文</Title><Table size="small" rowKey={(row) => (row.edge_ids ?? []).join('|')} dataSource={report.candidate_context_paths} columns={contextPathColumns} pagination={{ pageSize: 5, showSizeChanger: false }} scroll={{ x: 800 }} /><Text type="secondary">ChEMBL target / UniProt 组件 / Reactome 参与关系仅提供上下文，不是调控或 ER+ 疗效结论。</Text></>}
        <div style={{ marginTop: 12 }}><Text strong>未解决缺口</Text><div style={{ marginTop: 6 }}><Space wrap>{report.evidence_gaps.map((gap) => <Tag key={gap} color="orange">{gap}</Tag>)}</Space></div></div>
        <Text type="secondary">不生成综合疗效概率；S2 WTCS、基因表达响应、文献背景和图谱关系保持为独立证据通道。</Text>
      </Card>}
      <Card title="单药证据机制图" className="section-card" extra={<Space wrap>
        <Button aria-label="放大机制图" onClick={() => { const graph = graphInstance.current; if (graph) graph.zoom({ level: Math.min(graph.maxZoom(), graph.zoom() * 1.2), renderedPosition: { x: graph.width() / 2, y: graph.height() / 2 } }) }}>放大</Button>
        <Button aria-label="缩小机制图" onClick={() => { const graph = graphInstance.current; if (graph) graph.zoom({ level: Math.max(graph.minZoom(), graph.zoom() / 1.2), renderedPosition: { x: graph.width() / 2, y: graph.height() / 2 } }) }}>缩小</Button>
        <Button onClick={() => graphInstance.current?.fit(undefined, 48)}>适配画布</Button>
        <Button onClick={() => graphInstance.current?.layout({ name: 'concentric', animate: false, fit: true, padding: 48, minNodeSpacing: 38, avoidOverlap: true, spacingFactor: 1.25 }).run()}>重置布局</Button>
      </Space>}>
        <Alert type="info" showIcon message="边表示各自来源的证据类型，虚线表示关联或 S1 交集" description="图中不自动补出药物—ER+ 疾病因果边。点击节点查看实体和条件；点击关系边查看来源记录。没有数字化证据等级或系统矛盾审查标记时，会明确显示未评定。" style={{ marginBottom: 12 }} />
        <Space wrap style={{ marginBottom: 12 }}>
          <Select aria-label="按实体类型筛选图节点" mode="multiple" allowClear maxTagCount="responsive" placeholder="全部节点类型" style={{ minWidth: 190, maxWidth: 360 }} value={graphNodeKinds} options={graphNodeTypeOptions} onChange={setGraphNodeKinds} />
          <Select aria-label="按关系类型筛选机制图" mode="multiple" allowClear maxTagCount="responsive" placeholder="全部关系类型" style={{ minWidth: 210, maxWidth: 390 }} value={graphRelations} options={graphRelationOptions} onChange={setGraphRelations} />
          <Select aria-label="按证据类别筛选机制图" mode="multiple" allowClear maxTagCount="responsive" placeholder="全部证据类别" style={{ minWidth: 210, maxWidth: 390 }} value={graphEvidenceCategories} options={graphEvidenceOptions} onChange={setGraphEvidenceCategories} />
          <Select aria-label="键盘选择节点查看详情" showSearch optionFilterProp="label" placeholder="选择节点查看详情" style={{ minWidth: 220, maxWidth: 360 }} options={mechanismModel.nodes.map((node) => ({ value: node.id, label: `${node.label} · ${node.kind}` }))} onChange={(id) => { const node = mechanismModel.nodes.find((item) => item.id === id); if (node) setSelectedGraphNode(node) }} />
          <Select aria-label="键盘选择关系查看证据" showSearch optionFilterProp="label" placeholder="选择关系查看证据" style={{ minWidth: 220, maxWidth: 360 }} options={mechanismModel.edges.map((edge) => ({ value: edge.id, label: `${edge.relation} · ${edge.category}` }))} onChange={(id) => { const edge = mechanismModel.edges.find((item) => item.id === id); if (edge) setSelectedGraphEdge(edge) }} />
          <Tag color="green">候选药物</Tag><Tag color="blue">靶点/基因</Tag><Tag color="cyan">蛋白</Tag><Tag color="purple">通路</Tag>
        </Space>
        {mechanismModel.truncated && <Alert type="warning" showIcon message="图中关系数达到 120 条上限，已优先显示靶点和证据关系；请用筛选器聚焦查看。" style={{ marginBottom: 12 }} />}
        {mechanismModel.edges.length === 0 ? <Empty description="该候选当前没有可展示的靶点、通路或表达关系；证据缺口仍保留在下方档案。" /> : <MechanismGraph elements={visibleGraph} onNode={onGraphNode} onEdge={onGraphEdge} onReady={onGraphReady} />}
        {selectedGraphNode && <Card size="small" title={<Space><Text>{selectedGraphNode.label}</Text><Tag>{selectedGraphNode.kind}</Tag></Space>} extra={<Button size="small" onClick={() => setSelectedGraphNode(null)}>关闭详情</Button>} style={{ marginTop: 12 }}><Space direction="vertical"><Text code>{selectedGraphNode.id}</Text><pre style={{ maxHeight: 220, overflow: 'auto', whiteSpace: 'pre-wrap' }}>{JSON.stringify(selectedGraphNode.detail, null, 2)}</pre></Space></Card>}
      </Card>
      <Modal title={`关系证据 · ${selectedGraphEdge?.relation ?? ''}`} open={!!selectedGraphEdge} onCancel={() => setSelectedGraphEdge(null)} footer={<Button onClick={() => setSelectedGraphEdge(null)}>关闭</Button>} width={760}>
        {selectedGraphEdge && (() => {
          const evidence = selectedGraphEdge.evidence
          const textValue = (keys: string[]) => keys.map((key) => evidence[key]).find((value) => value !== undefined && value !== null && String(value).trim() !== '')
          const sourceUrl = textValue(['source_url', 'ref_url', 'url'])
          const publication = textValue(['pmid', 'PMID', 'publications', 'source_publication', 'document_id', 'mechanism_refs'])
          const conditionKeys = Object.keys(evidence).filter((key) => /assay|organism|cell.line|dose|time|sig_id|activity.value|condition/i.test(key) && evidence[key] !== undefined && evidence[key] !== '')
          return <Space direction="vertical" style={{ width: '100%' }}>
            <DescriptionsLike values={{ 起点: selectedGraphEdge.source, 终点: selectedGraphEdge.target, 关系方向: selectedGraphEdge.directed ? '箭头由起点指向终点' : '无方向的集合交集', 证据类别: String(evidence.evidence_category ?? selectedGraphEdge.category), 作用方向: String(evidence.action_type ?? evidence.direction ?? '来源未明确标注') }} />
            <Text>来源数据库：{String(evidence.source_database ?? evidence.source ?? evidence.source_release ?? '未结构化标注')}</Text>
            {sourceUrl ? <a href={String(sourceUrl)} target="_blank" rel="noreferrer">打开原始来源记录</a> : <Text type="secondary">未提供可直接打开的来源 URL</Text>}
            <Text>文献 / 原始记录：{String(publication ?? evidence.source_record_id ?? evidence.source_record ?? '未返回 PMID 或记录号')}</Text>
            <Text>实验条件：{conditionKeys.length ? conditionKeys.map((key) => `${key}: ${String(evidence[key])}`).join(' · ') : '当前关系没有 assay/剂量/时间等结构化条件'}</Text>
            <Text>证据等级：未建立统一等级，不能从来源类型自动推定。</Text>
            <Text>矛盾证据：当前关系未进行系统冲突标注；“未标注”不等于不存在矛盾研究。</Text>
            <Typography.Title level={5}>来源证据字段</Typography.Title><pre style={{ maxHeight: 280, overflow: 'auto', whiteSpace: 'pre-wrap' }}>{JSON.stringify(evidence, null, 2)}</pre>
          </Space>
        })()}
      </Modal>
      <Card title="证据关系路径" className="section-card">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 12, alignItems: 'stretch' }}>
          <PathColumn title="候选药物" tone="#eaf7ef"><Text strong>{data.candidate.pert_iname}</Text><Text type="secondary">{String(data.candidate.identity?.graph_drug_id ?? '无本地图谱 Drug ID')}</Text><Text type="secondary">WTCS {fmt(data.candidate.wtcs)}</Text></PathColumn>
          <PathColumn title={`有来源直接作用证据 · ${data.counts.direct_target_assertions}`} tone="#edf4ff"><Space wrap>{targetRows.filter((row) => row.kind === 'direct').slice(0, 12).map((row) => <Button key={row.key} size="small" onClick={() => { setEvidenceKind('direct'); setQuery(row.symbol) }}>{row.symbol}</Button>)}</Space><Text type="secondary">ENZYME、TRANSPORTER 等其他关联单独列示。</Text></PathColumn>
          <PathColumn title={`S1 通路交汇 · ${data.counts.distinct_pathways}`} tone="#f4efff"><Space wrap>{data.pathways.slice(0, 12).map((pathway) => <Button key={pathway.id} size="small" onClick={() => setSelectedPathwayId(pathway.id)}>{pathway.label}</Button>)}</Space><Text type="secondary">基于靶点边与项目富集基因/通路关系的交集；不表示靶点直接参与或调控通路。</Text></PathColumn>
          <PathColumn title="ER+ 疾病背景" tone="#fff4e8"><Text>研究对象：ER 阳性乳腺癌</Text><Text type="secondary">现有交汇证据不自动构成 ER+ 特异关联</Text></PathColumn>
        </div>
      </Card>
      <Card title="药物—靶点证据" className="section-card">
        <Space wrap style={{ marginBottom: 12 }}><Input.Search aria-label="筛选靶点证据" placeholder="按基因、关系或来源筛选" allowClear style={{ width: 300 }} onChange={(event) => setQuery(event.target.value)} /><Select aria-label="按证据类型筛选" value={evidenceKind} onChange={setEvidenceKind} options={[{ value: 'all', label: '直接证据与一般关联' }, { value: 'direct', label: '直接作用证据' }, { value: 'association', label: '药物—基因关联' }]} style={{ width: 220 }} /><Select aria-label="按证据来源筛选" value={targetSource} onChange={setTargetSource} options={[{ value: 'all', label: '全部来源' }, { value: 'public', label: 'OptimusKG' }, { value: 'external', label: '外部补充证据' }]} style={{ width: 200 }} /></Space>
        <Table rowKey="key" size="small" columns={targetColumns} dataSource={targetRows} pagination={{ pageSize: 8, showSizeChanger: false }} locale={{ emptyText: '该候选当前没有符合筛选条件的证据' }} />
      </Card>
      <Card title="ChEMBL / DGIdb 独立数据库证据" className="section-card">
        <Alert type="warning" showIcon message={`ChEMBL mechanism ${data.chembl_mechanisms.length} 条；活性记录 ${data.source_evidence_summary.chembl_activity_records_saved} 条（${data.source_evidence_summary.chembl_activity_status}）；DGIdb 精确药名互动 ${data.dgidb_interactions.length} 条`} description="这里展示数据库返回的独立证据记录，不等同于本地已复核并纳入专项图谱的直接靶点。ChEMBL assay 活性是实验关联，不能单独定性机制；DGIdb 汇总互动也可能是间接或计算推断。" style={{ marginBottom: 12 }} />
        <Typography.Title level={5}>ChEMBL mechanism</Typography.Title>
        <Table rowKey={(row) => `${row.molecule_chembl_id}:${row.mechanism_id}:${row.target_chembl_id}`} size="small" columns={chemblColumns} dataSource={chemblRows} pagination={false} locale={{ emptyText: 'ChEMBL mechanism 端点未返回记录；不表示无靶点知识' }} />
        <Typography.Title level={5} style={{ marginTop: 20 }}>DGIdb 精确药名互动</Typography.Title>
        <Table rowKey={(row) => `${row.dgidb_drug_id}:${row.gene_concept_id}:${row.sources}`} size="small" columns={dgidbColumns} dataSource={data.dgidb_interactions} pagination={{ pageSize: 6, showSizeChanger: false }} locale={{ emptyText: '没有按冻结候选精确名称返回的 DGIdb 互动' }} scroll={{ x: 900 }} />
      </Card>
      <Card title="靶点与 S1 富集通路交汇" className="section-card">{selectedPathwayId && <Space style={{ marginBottom: 12 }}><Tag color="purple">{pathwayNames.get(selectedPathwayId) ?? selectedPathwayId}</Tag><Button size="small" onClick={() => setSelectedPathwayId(undefined)}>清除通路筛选</Button></Space>}<Table rowKey={(row) => `${row.target_gene_id}:${row.pathway_id}`} size="small" columns={routeColumns} dataSource={data.pathway_routes.filter((row) => !selectedPathwayId || row.pathway_id === selectedPathwayId)} pagination={{ pageSize: 8, showSizeChanger: false }} locale={{ emptyText: '当前没有可核查的靶点—S1 通路交汇' }} /></Card>
      <Card title={`Reactome 靶点组件通路映射 · ${data.reactome_pathways.length}`} className="section-card"><Alert type="info" showIcon message={`Reactome ${data.provenance.reactome_release ?? 'release'} 人类映射；${new Set(data.reactome_pathways.map((row) => row.pathway_id)).size} 个不同通路`} description="按 ChEMBL mechanism 的人类 UniProt 靶点组件查询 Reactome。此处代表组件参与/映射，不表示药物激活或抑制通路；ChEMBL 蛋白家族靶点仍保留为家族组件语义。" style={{ marginBottom: 12 }} /><Table rowKey={(row) => `${row.chembl_target_id}:${row.uniprot_accession}:${row.pathway_id}`} size="small" columns={reactomeColumns} dataSource={data.reactome_pathways} pagination={{ pageSize: 8, showSizeChanger: false }} scroll={{ x: 800 }} locale={{ emptyText: '本候选没有已抓取的 ChEMBL mechanism 靶点组件或 Reactome 映射' }} /></Card>
      <Card title="S1 / S2 表达证据" className="section-card"><Alert type="info" showIcon message="LINCS COMPZ 是转录响应值" description="它不是药物与靶点结合、靶点活性或疗效的直接测量。S1/S2 方向比较为描述性整合。" style={{ marginBottom: 12 }} /><Table rowKey={(row) => `${row.target_gene_id}:${row.sig_id}`} size="small" columns={expressionColumns} dataSource={data.expression_evidence} pagination={{ pageSize: 8, showSizeChanger: false }} locale={{ emptyText: '该候选没有可连接的靶点 S1/S2 表达证据' }} /></Card>
      <Card title="全基因 S1/S2 方向交叉" className="section-card"><Alert type="info" showIcon message={`冻结签名中 ${data.expression_reversal_summary.measured_gene_symbols} 个基因可测；其中 ${data.expression_reversal_summary.S1_significant_overlap} 个与 S1 显著基因交叉`} description={`方向相反 ${data.expression_reversal_summary.opposite_direction} 个，同向 ${data.expression_reversal_summary.same_direction} 个，中性 ${data.expression_reversal_summary.neutral} 个。只取该候选冻结的单条 Level 5 共识 sig_id；COMPZ 是转录响应，方向相反不代表靶点抑制或治疗作用。`} style={{ marginBottom: 12 }} /><Space wrap style={{ marginBottom: 12 }}><Input.Search aria-label="筛选方向交叉基因" placeholder="按基因符号或 Ensembl ID 筛选" allowClear style={{ width: 300 }} onChange={(event) => setExpressionQuery(event.target.value)} /><Select aria-label="按表达方向交叉筛选" value={expressionFilter} onChange={setExpressionFilter} options={[{ value: 'all', label: '显著 S1 交叉基因' }, { value: 'OPPOSITE', label: 'S1/S2 方向相反' }, { value: 'SAME', label: 'S1/S2 同向' }, { value: 'NEUTRAL', label: 'S2 中性' }]} style={{ width: 200 }} /></Space><Table rowKey={(row) => `${row.pert_id}:${row.gene_symbol}`} size="small" columns={reversalColumns} dataSource={reversalRows} pagination={{ pageSize: 12, showSizeChanger: false, showTotal: (total) => `共 ${total} 个基因` }} locale={{ emptyText: '没有符合筛选条件的基因' }} /></Card>
      <Card title="Exp006–Exp011 历史稳健性与外部复核" className="section-card"><Alert type="warning" showIcon message="历史分析结果，不是本轮重算" description="展示剂量/QC、签名基因集、置换、独立 S1 和 PRISM 复核。缺行表示当时未覆盖或未匹配；PRISM 细胞存活终点不能与 WTCS 直接合并。" style={{ marginBottom: 12 }} /><Table rowKey="key" size="small" columns={robustnessColumns} dataSource={robustnessRows} pagination={false} scroll={{ x: 950 }} /></Card>
      <Card title="ER+ 疾病背景文献筛查" className="section-card"><Alert type="warning" showIcon message="定向文献筛查，不是系统综述" description="区分 ER+ 临床证据、ER+ 前临床模型、混合亚型研究和证据缺口。关系图将人工审查记录建模为带来源与限制的疾病证据节点；路径表示研究上下文，不表示药物治疗该疾病或存在疗效。" style={{ marginBottom: 12 }} /><Table rowKey={(row) => row.source_id} size="small" columns={diseaseColumns} dataSource={data.disease_evidence} pagination={false} locale={{ emptyText: '该候选尚无整理的疾病背景记录' }} /></Card>
      <Card title="数据来源与版本"><Space direction="vertical"><Text>公共图谱：{data.provenance.public_kg_release}</Text><Text>Top 10 榜单 SHA-256：<Text code>{data.provenance.top10_source_sha256}</Text></Text><Text>外部证据 overlay SHA-256：<Text code>{data.provenance.external_overlay_sha256}</Text></Text><Text>离线 bundle manifest SHA-256：<Text code>{data.provenance.bundle_manifest_sha256}</Text></Text></Space></Card>
      <Alert type="info" showIcon message="解释边界" description={data.interpretation} />
    </>}
  </Space>
}

function PathColumn({ title, tone, children }: { title: string; tone: string; children: ReactNode }) {
  return <div style={{ background: tone, borderRadius: 12, border: '1px solid #e8e8ed', padding: 16, minHeight: 130, display: 'flex', flexDirection: 'column', gap: 8 }}><Text strong>{title}</Text>{children}</div>
}

function DescriptionsLike({ values }: { values: Record<string, string> }) {
  return <Row gutter={[16, 10]}>{Object.entries(values).map(([key, value]) => <Col xs={24} md={8} key={key}><Text type="secondary">{key}: </Text><Text>{value || '—'}</Text></Col>)}</Row>
}
