import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Alert, Button, Card, Empty, Input, Modal, Select, Space, Spin, Tag, Typography, message } from 'antd'
import type { ElementDefinition } from 'cytoscape'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { api, GraphNode, Subgraph, isGraphBuildQueryable } from '../api'
import { Loading, useProject } from '../projectContext'
import { graphTypeLabel, runTypeLabel, statusLabel } from '../locales/zh-CN'
import { palette } from '../designTokens'

const { Title, Text } = Typography

function GraphCanvas({ elements, onSelect, onEvidence }: { elements: ElementDefinition[]; onSelect: (node: GraphNode) => void; onEvidence:(ids:string[])=>void }) {
  const container = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!container.current) return
    let disposed = false
    let destroyGraph: (() => void) | undefined
    void import('cytoscape').then(({ default: cytoscape }) => {
      if (disposed || !container.current) return
      const cy = cytoscape({
      container: container.current,
      elements,
      layout: { name: 'cose', animate: false, nodeRepulsion: 5200, idealEdgeLength: 72, edgeElasticity: 100, gravity: 0.22, numIter: 700 },
      style: [
        { selector: 'node', style: { label: 'data(label)', color: palette.graph.text, 'font-size': 8, 'text-wrap': 'wrap', 'text-max-width': '84px', 'text-outline-color': '#fff', 'text-outline-width': 1, width: 28, height: 28, 'background-color': palette.graph.node } },
        { selector: 'node[type="Drug"]', style: { 'background-color': palette.graph.drug, width: 34, height: 34 } },
        { selector: 'node[type="Pathway"]', style: { 'background-color': palette.graph.pathway, shape: 'diamond' } },
        { selector: 'node[type="Candidate"]', style: { 'background-color': palette.graph.candidate, shape: 'round-rectangle' } },
        { selector: 'edge', style: { width: 1, 'line-color': palette.graph.edge, 'target-arrow-color': palette.graph.arrow, 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', label: 'data(label)', color: palette.graph.edgeText, 'font-size': 5, 'text-background-color': '#fff', 'text-background-opacity': 0.82, 'text-background-padding': '1px' } },
        { selector: 'node:selected', style: { 'border-width': 3, 'border-color': palette.primary, 'z-index': 20 } },
        { selector: 'edge:selected', style: { width: 3, 'line-color': palette.primary, 'target-arrow-color': palette.primary, 'z-index': 20 } },
        { selector: 'node.path-highlight', style: { 'background-color': palette.graph.highlight, 'border-width': 3, 'border-color': palette.graph.highlightBorder, 'z-index': 10 } },
        { selector: 'edge.path-highlight', style: { width: 4, 'line-color': palette.graph.highlight, 'target-arrow-color': palette.graph.highlight, 'z-index': 10 } },
      ],
      })
      destroyGraph = () => cy.destroy()
      cy.on('tap', 'node', (event) => {
        const node = event.target.data()
        onSelect({ id: node.id, type: node.type, label: node.label, properties: JSON.parse(node.detail || '{}') })
      })
      cy.on('tap', 'edge', (event) => {
        const evidenceIds = event.target.data().evidenceIds
        if (Array.isArray(evidenceIds) && evidenceIds.length) onEvidence(evidenceIds)
      })
    })
    return () => { disposed = true; destroyGraph?.() }
  }, [elements, onSelect, onEvidence])
  return <div ref={container} style={{ width: '100%', height: 620 }} />
}

function shortestLoadedPath(edges: Subgraph['edges'], start?: string, end?: string) {
  if (!start || !end || start === end) return { nodeIds: new Set<string>(), edgeIds: new Set<string>() }
  const adjacency = new Map<string, Array<{ nodeId: string; edgeId: string }>>()
  for (const edge of edges) {
    adjacency.set(edge.source, [...(adjacency.get(edge.source) ?? []), { nodeId: edge.target, edgeId: edge.id }])
    adjacency.set(edge.target, [...(adjacency.get(edge.target) ?? []), { nodeId: edge.source, edgeId: edge.id }])
  }
  const queue = [start]
  const previous = new Map<string, { nodeId: string; edgeId: string }>()
  const visited = new Set([start])
  for (let index = 0; index < queue.length && !visited.has(end); index++) {
    const current = queue[index]
    for (const next of adjacency.get(current) ?? []) {
      if (visited.has(next.nodeId)) continue
      visited.add(next.nodeId)
      previous.set(next.nodeId, { nodeId: current, edgeId: next.edgeId })
      queue.push(next.nodeId)
    }
  }
  if (!visited.has(end)) return { nodeIds: new Set<string>(), edgeIds: new Set<string>() }
  const nodeIds = new Set([end])
  const edgeIds = new Set<string>()
  let current = end
  while (current !== start) {
    const step = previous.get(current)
    if (!step) break
    nodeIds.add(step.nodeId)
    edgeIds.add(step.edgeId)
    current = step.nodeId
  }
  return { nodeIds, edgeIds }
}

export default function GraphPage() {
  const { project } = useProject()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [selected,setSelected]=useState<GraphNode|null>(null)
  const [selectedEvidenceId,setSelectedEvidenceId]=useState<string>()
  const showGraphEvidence=useCallback((ids:string[])=>{if(ids[0])setSelectedEvidenceId(ids[0])},[])
  const [searchText,setSearchText]=useState('')
  const [searchTerm,setSearchTerm]=useState('')
  const [centerNodeId,setCenterNodeId]=useState<string>()
  const [cursor,setCursor]=useState(0)
  const [loaded,setLoaded]=useState<Subgraph|null>(null)
  const [nodeTypeFilter,setNodeTypeFilter]=useState<string[]>([])
  const [relationFilter,setRelationFilter]=useState<string[]>([])
  const [edgeScope,setEdgeScope]=useState<'all'|'direct_target'|'context'>('all')
  const [pathStart,setPathStart]=useState<string>()
  const [pathEnd,setPathEnd]=useState<string>()
  const [selectedBuildId,setSelectedBuildId]=useState<string>()
  const builds=useQuery({queryKey:['graph-builds',project?.project_id],queryFn:()=>api.graphBuilds(project!.project_id),enabled:!!project})
  const queryableBuilds=(builds.data?.items??[]).filter(isGraphBuildQueryable)
  const runs=useQuery({queryKey:['project-runs',project?.project_id],queryFn:()=>api.runs(project!.project_id),enabled:!!project})
  const [bundleS1,setBundleS1]=useState<string>()
  const [bundleS2,setBundleS2]=useState<string>()
  const [bundleEnrichment,setBundleEnrichment]=useState<string>()
  const graphBundleRuns=(runs.data??[]).filter(run=>run.run_type==='kg_graph_bundle'&&run.status==='completed')
  const latestBundleId=graphBundleRuns[0]?.analysis_run_id
  const activeBuildId=selectedBuildId??searchParams.get('graph_build_id')??queryableBuilds[0]?.graph_build_id
  const pathPertId=searchParams.get('pert_id')??undefined
  const requestedPathId=searchParams.get('path_id')??undefined
  const pathPackage=useQuery({queryKey:['kg06-path-package',project?.project_id,pathPertId,activeBuildId],queryFn:()=>api.kg06Package(project!.project_id,pathPertId!,activeBuildId),enabled:!!project&&!!pathPertId&&!!requestedPathId&&!!activeBuildId})
  const requestedPath=(pathPackage.data?.paths??[]).find((path:Record<string,any>)=>path.path_id===requestedPathId)
  const activeGraphSummary=useQuery({queryKey:['graph-summary',project?.project_id,activeBuildId],queryFn:()=>api.graphSummary(project!.project_id,activeBuildId),enabled:!!project&&!!activeBuildId})
  const suggestions=useQuery({queryKey:['graph-search',project?.project_id,searchTerm,activeBuildId],queryFn:()=>api.searchNodes(project!.project_id,searchTerm,activeBuildId),enabled:!!project&&searchTerm.length>=2})
  const graphEvidence=useQuery({queryKey:['graph-evidence',selectedEvidenceId,activeBuildId],queryFn:()=>api.evidence(selectedEvidenceId!,activeBuildId),enabled:!!selectedEvidenceId})
  const q=useQuery({queryKey:['graph',project?.project_id,activeBuildId,centerNodeId,cursor],queryFn:()=>api.graph(project!.project_id,cursor,centerNodeId,activeBuildId),enabled:!!project})
  const registerBuild=useMutation({mutationFn:()=>api.registerGraphSnapshot(project!.project_id),onSuccess:async()=>{message.success('已登记并标记图谱版本');await Promise.all([queryClient.invalidateQueries({queryKey:['graph-builds',project?.project_id]}),queryClient.invalidateQueries({queryKey:['graph',project?.project_id]}),queryClient.invalidateQueries({queryKey:['graph-search',project?.project_id]})])},onError:(error:Error)=>message.error(error.message)})
  const createBundle=useMutation({mutationFn:()=>api.createProjectGraphBundle(project!.project_id,{s1_analysis_run_id:bundleS1!,s2_analysis_run_id:bundleS2!,enrichment_analysis_run_id:bundleEnrichment!}),onSuccess:async result=>{message.success(`GraphBundle 已生成：${result.analysis_run_id}`);await queryClient.invalidateQueries({queryKey:['project-runs',project?.project_id]})},onError:(error:Error)=>message.error(error.message)})
  const importBundle=useMutation({mutationFn:()=>api.buildProjectGraph(project!.project_id,latestBundleId),onSuccess:async()=>{message.success('已从最新 GraphBundle 构建图谱版本');await Promise.all([queryClient.invalidateQueries({queryKey:['graph-builds',project?.project_id]}),queryClient.invalidateQueries({queryKey:['graph',project?.project_id]}),queryClient.invalidateQueries({queryKey:['graph-search',project?.project_id]})])},onError:(error:Error)=>message.error(error.message)})
  useEffect(()=>{setCenterNodeId(undefined);setCursor(0);setLoaded(null);setSelected(null);setSelectedBuildId(undefined);setSearchText('');setSearchTerm('');setNodeTypeFilter([]);setRelationFilter([]);setEdgeScope('all');setPathStart(undefined);setPathEnd(undefined)},[project?.project_id])
  useEffect(()=>{if(!q.data)return;setLoaded(previous=>{if(cursor===0||!previous)return q.data;const nodes=new Map(previous.nodes.map(n=>[n.id,n]));q.data.nodes.forEach(n=>nodes.set(n.id,n));const edges=new Map(previous.edges.map(e=>[e.id,e]));q.data.edges.forEach(e=>edges.set(e.id,e));return {...q.data,nodes:[...nodes.values()],edges:[...edges.values()]}})},[q.data,cursor])
  const baseGraphData=loaded??q.data
  const graphData=useMemo(()=>{
    if(!baseGraphData||!requestedPath)return baseGraphData
    const nodes=new Map(baseGraphData.nodes.map(node=>[node.id,node]))
    ;(requestedPath.nodes??[]).forEach((node:Record<string,any>)=>nodes.set(node.id,{id:node.id,type:node.type,label:node.label,properties:{}}))
    const edges=new Map(baseGraphData.edges.map(edge=>[edge.id,edge]))
    ;(requestedPath.edges??[]).forEach((edge:Record<string,any>)=>edges.set(edge.edge_id,{id:edge.edge_id,source:edge.source_id,target:edge.target_id,relation:edge.relation_type,evidence_ids:edge.evidence_ids??[]}))
    return {...baseGraphData,nodes:[...nodes.values()],edges:[...edges.values()]}
  },[baseGraphData,requestedPath])
  const graphNodeTypes=new Map((graphData?.nodes??[]).map(node=>[node.id,node.type]))
  const nodeTypes=[...new Set((graphData?.nodes??[]).map(node=>node.type))].sort()
  const relationTypes=[...new Set((graphData?.edges??[]).map(edge=>edge.relation))].sort()
  const visibleNodes=(graphData?.nodes??[]).filter(node=>nodeTypeFilter.length===0||nodeTypeFilter.includes(node.type))
  const visibleNodeIds=new Set(visibleNodes.map(node=>node.id))
  const isDirectDrugTarget=(edge:Subgraph['edges'][number])=>(graphNodeTypes.get(edge.source)==='Drug'&&['Gene','ProteinTarget'].includes(graphNodeTypes.get(edge.target)??''))||(graphNodeTypes.get(edge.target)==='Drug'&&['Gene','ProteinTarget'].includes(graphNodeTypes.get(edge.source)??''))
  const visibleEdges=(graphData?.edges??[]).filter(edge=>visibleNodeIds.has(edge.source)&&visibleNodeIds.has(edge.target)&&(relationFilter.length===0||relationFilter.includes(edge.relation))&&(edgeScope==='all'||(edgeScope==='direct_target'?isDirectDrugTarget(edge):!isDirectDrugTarget(edge))))
  const baseHighlight=shortestLoadedPath(visibleEdges,pathStart,pathEnd)
  const highlighted=requestedPath?{nodeIds:new Set([...(requestedPath.nodes??[]).map((node:Record<string,any>)=>node.id),...baseHighlight.nodeIds]),edgeIds:new Set([...(requestedPath.edges??[]).map((edge:Record<string,any>)=>edge.edge_id),...baseHighlight.edgeIds])}:baseHighlight
  const elements=useMemo(()=>[
    ...visibleNodes.map(node=>({data:{id:node.id,label:node.label,type:node.type,detail:JSON.stringify(node.properties)},classes:highlighted.nodeIds.has(node.id)?'path-highlight':''})),
    ...visibleEdges.map(edge=>({data:{id:edge.id,source:edge.source,target:edge.target,label:edge.relation,evidenceIds:edge.evidence_ids},classes:highlighted.edgeIds.has(edge.id)?'path-highlight':''})),
  ],[visibleNodes,visibleEdges,highlighted])
  if(q.isLoading)return <Loading/>;if(q.error)return <Loading error={q.error as Error}/>
  const searchOptions=(suggestions.data?.items??[]).map(node=>({value:node.id,label:`${node.label}（${graphTypeLabel(node.type)}）`}))
  const exportGraph=()=>{const blob=new Blob([JSON.stringify({...graphData,nodes:visibleNodes,edges:visibleEdges},null,2)],{type:'application/json'});const anchor=document.createElement('a');anchor.href=URL.createObjectURL(blob);anchor.download='subgraph.json';anchor.click();URL.revokeObjectURL(anchor.href)}
  const nodeOptions=visibleNodes.map(node=>({value:node.id,label:`${node.label}（${graphTypeLabel(node.type)}）`}))
  return <>{requestedPathId&&pathPackage.isLoading&&<Alert type="info" message="正在载入所选机制路径…"/>}{pathPackage.error&&<Alert type="error" message="路径证据包读取失败" description={(pathPackage.error as Error).message}/ >}{requestedPathId&&pathPackage.data&&!requestedPath&&<Alert type="warning" message="所选 Path ID 不属于当前项目与图谱版本"/>}{requestedPath&&<Alert type="success" showIcon message={`正在高亮路径 ${requestedPathId} · ${requestedPath.route_type}`} description="节点和边来自当前项目指定 GraphBuild 的 KG06 证据包；点击边可查看 Evidence ID。"/>}<div className="page-heading"><div><Text className="eyebrow">机制探索 / 公共知识图谱</Text><Title level={2}>局部证据子图</Title><Text type="secondary">当前已加载 {graphData?.nodes.length??0} 个节点；API 单页最多 100 个、查询深度最多 2 跳。所选 KG06 路径会按原始 Path ID 高亮对应节点和边。</Text></div><Button onClick={exportGraph}>导出当前筛选子图</Button></div><Card title="项目图谱构建" className="section-card"><Space direction="vertical" style={{width:'100%'}}><Alert type="info" showIcon message="生成可追溯的项目 GraphBundle" description="只使用同一项目中已完成且相互关联的 S1、S2 和通路富集运行；药物按 InChIKey 精确映射，剂量和时间条件分别保留。"/><Space wrap><Select style={{width:300}} placeholder="选择已完成的 S1 运行" value={bundleS1} options={(runs.data??[]).filter(run=>['s1_precomputed_deg','s1_limma_microarray','s1_rnaseq_edger_voom'].includes(run.run_type)&&run.status==='completed').map(run=>({value:run.analysis_run_id,label:`${runTypeLabel(run.run_type)} · ${run.analysis_run_id}`}))} onChange={setBundleS1}/><Select style={{width:300}} placeholder="选择关联的 S2 运行" value={bundleS2} options={(runs.data??[]).filter(run=>run.run_type==='s2_lincs'&&run.status==='completed').map(run=>({value:run.analysis_run_id,label:`${runTypeLabel(run.run_type)} · ${run.analysis_run_id}`}))} onChange={setBundleS2}/><Select style={{width:300}} placeholder="选择关联的富集运行" value={bundleEnrichment} options={(runs.data??[]).filter(run=>run.run_type==='s1_pathway_enrichment'&&run.status==='completed').map(run=>({value:run.analysis_run_id,label:`${runTypeLabel(run.run_type)} · ${run.analysis_run_id}`}))} onChange={setBundleEnrichment}/><Button type="primary" disabled={!bundleS1||!bundleS2||!bundleEnrichment} loading={createBundle.isPending} onClick={()=>createBundle.mutate()}>生成 GraphBundle</Button><Button disabled={!latestBundleId} loading={importBundle.isPending} onClick={()=>importBundle.mutate()}>构建最新图谱版本</Button></Space><Text type="secondary">已生成 {graphBundleRuns.length} 个版本化 GraphBundle；新版本不会覆盖旧文件。</Text></Space></Card><Card title="图谱版本记录" className="section-card"><Space direction="vertical" style={{width:'100%'}}><Alert type="info" showIcon message="图谱版本登记与 Neo4j 数据关联" description="操作会校验输入 SHA-256，并将图谱关系幂等导入、标记所属版本；不删除已有版本。"/><Space><Select style={{minWidth:340}} value={activeBuildId} placeholder="选择图谱版本" options={queryableBuilds.map(build=>({value:build.graph_build_id,label:`${build.graph_build_id} · ${statusLabel(build.status)}`}))} onChange={id=>{setSelectedBuildId(id);setCursor(0);setLoaded(null);setCenterNodeId(undefined)}}/><Button type="primary" loading={registerBuild.isPending} onClick={()=>registerBuild.mutate()}>登记当前快照</Button><Text type="secondary">已登记 {builds.data?.items.length??0} 个版本，其中可查询 {queryableBuilds.length} 个</Text></Space><Text type="secondary">当前选中版本实时统计：{activeGraphSummary.data?`${activeGraphSummary.data.node_count} 个节点、${activeGraphSummary.data.edge_count} 条关系`:activeGraphSummary.isLoading?"读取中":"不可用"}</Text>{builds.error&&<Alert type="error" message="版本记录读取失败" description={(builds.error as Error).message}/>}{(builds.data?.items??[]).map(build=><Card size="small" key={build.graph_build_id}><Space direction="vertical"><Text code>{build.graph_build_id}</Text><Text type="secondary">状态：{build.status==='materialized'?'已导入 Neo4j 并按版本标记':build.status==='failed'?'导入失败':'待 Neo4j 版本标记'} · 来源：{build.graph_source} · 关联运行：{build.analysis_run_id}</Text><Text type="secondary">输入文件：{Object.keys(build.input_hashes).length} 项 · 登记时节点 {String(build.summary.node_count??'—')} · 登记时关系 {String(build.summary.edge_count??'—')}</Text></Space></Card>)}</Space></Card><div className="graph-workspace"><Card className="section-card graph-controls"><Space wrap><Input.Search value={searchText} placeholder="搜索药物、基因、通路或标准 ID" style={{width:320}} onChange={event=>setSearchText(event.target.value)} onSearch={setSearchTerm} enterButton="搜索"/><Select showSearch optionFilterProp="label" placeholder={searchTerm.length<2?'输入至少 2 个字符后搜索':'选择搜索结果'} style={{width:350}} options={searchOptions} loading={suggestions.isFetching} onChange={id=>{setCenterNodeId(id);setCursor(0);setLoaded(null);setSelected(null);setPathStart(undefined);setPathEnd(undefined)}}/><Button onClick={()=>{setSearchText('');setSearchTerm('');setCenterNodeId(undefined);setCursor(0);setLoaded(null);setSelected(null);setPathStart(undefined);setPathEnd(undefined)}}>清除搜索</Button>{graphData?.truncated&&<Button loading={q.isFetching} onClick={()=>setCursor(Number(graphData.next_cursor??cursor+100))}>加载下一页</Button>}<Select value={edgeScope} onChange={(value:'all'|'direct_target'|'context')=>setEdgeScope(value)} style={{width:230}} options={[{value:'all',label:'全部证据关系'},{value:'direct_target',label:'直接药物—靶点关系'},{value:'context',label:'其他疾病/通路关系'}]}/><Select mode="multiple" allowClear maxTagCount="responsive" placeholder="按节点类型筛选" style={{minWidth:210,maxWidth:360}} value={nodeTypeFilter} options={nodeTypes.map(type=>({value:type,label:graphTypeLabel(type)}))} onChange={setNodeTypeFilter}/><Select mode="multiple" allowClear maxTagCount="responsive" placeholder="按关系类型筛选" style={{minWidth:210,maxWidth:360}} value={relationFilter} options={relationTypes.map(type=>({value:type,label:graphTypeLabel(type)}))} onChange={setRelationFilter}/><Select showSearch optionFilterProp="label" allowClear placeholder="路径起点" style={{width:240}} value={pathStart} options={nodeOptions} onChange={setPathStart}/><Select showSearch optionFilterProp="label" allowClear placeholder="路径终点" style={{width:240}} value={pathEnd} options={nodeOptions} onChange={setPathEnd}/></Space>{pathStart&&pathEnd&&pathStart!==pathEnd&&highlighted.nodeIds.size===0&&<Alert type="warning" showIcon message="当前已加载的子图中未找到这两个节点之间的路径" style={{marginTop:12}}/>}</Card><Card className="graph-card"><GraphCanvas elements={elements} onSelect={setSelected} onEvidence={showGraphEvidence}/></Card><Card title="节点详情" className="detail-card">{selected?<><Title level={5}>{selected.label}</Title><Tag>{graphTypeLabel(selected.type)}</Tag><Text code>{selected.id}</Text><pre>{JSON.stringify(selected.properties,null,2)}</pre></>:<Empty description="点击图中节点查看属性"/>}</Card></div><Alert type="warning" showIcon message="解读限制" description="知识图谱关系表示可追溯的数据库断言与项目表达证据交集，不代表药物疗效。"/><Modal title="图谱来源证据" open={!!selectedEvidenceId} onCancel={()=>setSelectedEvidenceId(undefined)} footer={null} width={760}>{graphEvidence.isLoading?<Spin/>:graphEvidence.error?<Alert type="error" message="来源证据读取失败" description={(graphEvidence.error as Error).message}/>:<pre style={{maxHeight:500,overflow:'auto',whiteSpace:'pre-wrap'}}>{JSON.stringify(graphEvidence.data,null,2)}</pre>}</Modal></>
}
