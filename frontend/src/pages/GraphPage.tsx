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

function GraphCanvas({ elements, centerNodeId, onSelect, onEvidence }: { elements: ElementDefinition[]; centerNodeId?: string; onSelect: (node: GraphNode) => void; onEvidence:(edge:Subgraph['edges'][number])=>void }) {
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
      layout: centerNodeId
        ? { name: 'concentric', animate: false, fit: true, padding: 30, minNodeSpacing: 2, avoidOverlap: false, spacingFactor: 0.55, concentric: (node: any) => node.id() === centerNodeId ? 1000000 : node.degree(), levelWidth: () => 1 }
        : { name: 'grid', animate: false, fit: true, padding: 30, avoidOverlap: true, condense: true, rows: Math.ceil(Math.sqrt(elements.length / 2)) },
      minZoom: 0.05,
      maxZoom: 3,
      style: [
        { selector: 'node', style: { label: 'data(label)', color: palette.graph.text, 'font-size': 5, 'min-zoomed-font-size': 4, 'text-wrap': 'wrap', 'text-max-width': '48px', 'text-outline-color': '#fff', 'text-outline-width': 0.5, width: 14, height: 14, 'background-color': palette.graph.node } },
        { selector: 'node[type="Drug"]', style: { 'background-color': palette.graph.drug, width: 20, height: 20, shape: 'round-rectangle', 'font-weight': 700 } },
        { selector: 'node[type="Gene"], node[type="ProteinTarget"]', style: { 'background-color': palette.graph.node, shape: 'ellipse' } },
        { selector: 'node[type="Pathway"]', style: { 'background-color': palette.graph.pathway, shape: 'diamond' } },
        { selector: 'node[type="Candidate"]', style: { 'background-color': palette.graph.candidate, shape: 'round-rectangle' } },
        { selector: 'edge', style: { width: 1, 'line-color': palette.graph.edge, 'target-arrow-color': palette.graph.arrow, 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', label: centerNodeId ? 'data(label)' : '', color: palette.graph.edgeText, 'font-size': 6, 'text-background-color': '#fff', 'text-background-opacity': 0.94, 'text-background-padding': '1px' } },
        { selector: 'edge[directed = false]', style: { 'target-arrow-shape': 'none' } },
        { selector: 'node.query-center', style: { 'border-width': 4, 'border-color': palette.primary, 'z-index': 25 } },
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
        const edge = event.target.data()
        onEvidence({ id: edge.id, source: edge.source, target: edge.target, relation: edge.label, evidence_ids: edge.evidenceIds ?? [], directed: edge.directed })
      })
    })
    return () => { disposed = true; destroyGraph?.() }
  }, [elements, centerNodeId, onSelect, onEvidence])
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
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [selected,setSelected]=useState<GraphNode|null>(null)
  const [selectedEvidenceId,setSelectedEvidenceId]=useState<string>()
  const [selectedGraphEdge,setSelectedGraphEdge]=useState<Subgraph['edges'][number]|null>(null)
  const showGraphEvidence=useCallback((edge:Subgraph['edges'][number])=>{setSelectedGraphEdge(edge);setSelectedEvidenceId(edge.evidence_ids[0])},[])
  const [searchText,setSearchText]=useState(()=>searchParams.get('q')??'')
  const [searchTerm,setSearchTerm]=useState(()=>searchParams.get('q')??'')
  const [centerNodeId,setCenterNodeId]=useState<string|undefined>(()=>searchParams.get('node_id')??undefined)
  const [cursor,setCursor]=useState(0)
  const [loaded,setLoaded]=useState<Subgraph|null>(null)
  const [nodeTypeFilter,setNodeTypeFilter]=useState<string[]>([])
  const [relationFilter,setRelationFilter]=useState<string[]>([])
  const [edgeScope,setEdgeScope]=useState<'all'|'direct_target'|'context'>(()=>{
    const scope=searchParams.get('edge_scope')
    return scope==='direct_target'||scope==='context'?scope:'all'
  })
  const [pathStart,setPathStart]=useState<string>()
  const [pathEnd,setPathEnd]=useState<string>()
  const [selectedBuildId,setSelectedBuildId]=useState<string|undefined>(undefined)
  const builds=useQuery({queryKey:['graph-builds',project?.project_id],queryFn:()=>api.graphBuilds(project!.project_id),enabled:!!project})
  const queryableBuilds=(builds.data?.items??[]).filter(isGraphBuildQueryable)
  const runs=useQuery({queryKey:['project-runs',project?.project_id],queryFn:()=>api.runs(project!.project_id),enabled:!!project})
  const [bundleS1,setBundleS1]=useState<string>()
  const [bundleS2,setBundleS2]=useState<string>()
  const [bundleEnrichment,setBundleEnrichment]=useState<string>()
  const graphBundleRuns=(runs.data??[]).filter(run=>run.run_type==='kg_graph_bundle'&&run.status==='completed')
  useEffect(()=>{
    if(!runs.data)return
    const completeS1=runs.data.filter(run=>['s1_precomputed_deg','s1_limma_microarray','s1_rnaseq_edger_voom'].includes(run.run_type)&&run.status==='completed')
    const chosenS1=completeS1.find(run=>run.analysis_run_id===bundleS1)??completeS1[0]
    if(chosenS1?.analysis_run_id!==bundleS1)setBundleS1(chosenS1?.analysis_run_id)
    const s1Id=chosenS1?.analysis_run_id
    const compatibleS2=runs.data.filter(run=>run.run_type==='s2_lincs'&&run.status==='completed'&&run.parameters?.s1_analysis_run_id===s1Id)
    const compatibleEnrichment=runs.data.filter(run=>run.run_type==='s1_pathway_enrichment'&&run.status==='completed'&&run.parameters?.s1_analysis_run_id===s1Id)
    const chosenS2=compatibleS2.find(run=>run.analysis_run_id===bundleS2)??compatibleS2[0]
    const chosenEnrichment=compatibleEnrichment.find(run=>run.analysis_run_id===bundleEnrichment)??compatibleEnrichment[0]
    if(chosenS2?.analysis_run_id!==bundleS2)setBundleS2(chosenS2?.analysis_run_id)
    if(chosenEnrichment?.analysis_run_id!==bundleEnrichment)setBundleEnrichment(chosenEnrichment?.analysis_run_id)
  },[runs.data,bundleS1,bundleS2,bundleEnrichment])
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
  const activateBuild=(graphBuildId:string)=>{
    setSelectedBuildId(graphBuildId);setCursor(0);setLoaded(null);setCenterNodeId(undefined);setSearchText('');setSearchTerm('');setSelected(null);setSelectedGraphEdge(null);setSelectedEvidenceId(undefined)
    setSearchParams(previous=>{const next=new URLSearchParams(previous);next.set('graph_build_id',graphBuildId);['node_id','q','edge_scope','path_id','pert_id'].forEach(key=>next.delete(key));return next},{replace:true})
  }
  const refreshBuildViews=async()=>Promise.all([
    queryClient.invalidateQueries({queryKey:['graph-builds',project?.project_id]}),
    queryClient.invalidateQueries({queryKey:['graph-summary',project?.project_id]}),
    queryClient.invalidateQueries({queryKey:['graph',project?.project_id]}),
    queryClient.invalidateQueries({queryKey:['graph-search',project?.project_id]}),
  ])
  const registerBuild=useMutation({mutationFn:()=>api.registerGraphSnapshot(project!.project_id),onSuccess:async result=>{activateBuild(result.graph_build_id);message.success(`图谱版本已登记并选中：${result.graph_build_id}`);await refreshBuildViews()},onError:(error:Error)=>message.error(error.message)})
  const createBundle=useMutation({mutationFn:async()=>{
    const bundle=await api.createProjectGraphBundle(project!.project_id,{s1_analysis_run_id:bundleS1!,s2_analysis_run_id:bundleS2!,enrichment_analysis_run_id:bundleEnrichment!})
    try{return {bundle,build:await api.buildProjectGraph(project!.project_id,bundle.analysis_run_id)}}
    catch(error){throw new Error(`GraphBundle 已生成（${bundle.analysis_run_id}），但 GraphBuild 导入失败：${error instanceof Error?error.message:String(error)}`)}
  },onSuccess:async({build})=>{activateBuild(build.graph_build_id);message.success(`GraphBuild 已生成并切换展示：${build.graph_build_id}`);await Promise.all([refreshBuildViews(),queryClient.invalidateQueries({queryKey:['project-runs',project?.project_id]})])},onError:async(error:Error)=>{message.error(error.message);await Promise.all([queryClient.invalidateQueries({queryKey:['graph-builds',project?.project_id]}),queryClient.invalidateQueries({queryKey:['project-runs',project?.project_id]})])}})
  const importBundle=useMutation({mutationFn:(bundleRunId?:string)=>api.buildProjectGraph(project!.project_id,bundleRunId??latestBundleId),onSuccess:async result=>{activateBuild(result.graph_build_id);message.success(`GraphBuild 已生成并切换展示：${result.graph_build_id}`);await refreshBuildViews()},onError:async(error:Error)=>{message.error(error.message);await queryClient.invalidateQueries({queryKey:['graph-builds',project?.project_id]})}})
  const lastProjectId=useRef<string|undefined>(undefined)
  useEffect(()=>{
    if(!project?.project_id||lastProjectId.current===project.project_id)return
    const initialProject=lastProjectId.current===undefined
    lastProjectId.current=project.project_id
    setBundleS1(undefined);setBundleS2(undefined);setBundleEnrichment(undefined)
    setCenterNodeId(initialProject?searchParams.get('node_id')??undefined:undefined)
    setCursor(0);setLoaded(null);setSelected(null);setSelectedBuildId(undefined)
    setSearchText(initialProject?searchParams.get('q')??'':'');setSearchTerm(initialProject?searchParams.get('q')??'':'')
    setNodeTypeFilter([]);setRelationFilter([]);setEdgeScope(initialProject&&searchParams.get('edge_scope')==='direct_target'?'direct_target':initialProject&&searchParams.get('edge_scope')==='context'?'context':'all')
    setPathStart(undefined);setPathEnd(undefined)
    if(!initialProject)setSearchParams(previous=>{const next=new URLSearchParams(previous);['node_id','q','edge_scope','graph_build_id'].forEach(key=>next.delete(key));return next},{replace:true})
  },[project?.project_id,searchParams,setSearchParams])
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
  const isDirectDrugTarget=(edge:Subgraph['edges'][number])=>{
    const drugGenePair=(graphNodeTypes.get(edge.source)==='Drug'&&['Gene','ProteinTarget'].includes(graphNodeTypes.get(edge.target)??''))||(graphNodeTypes.get(edge.target)==='Drug'&&['Gene','ProteinTarget'].includes(graphNodeTypes.get(edge.source)??''))
    return drugGenePair&&['TARGET','TARGETS','INHIBITOR','AGONIST','ANTAGONIST','BLOCKER','PARTIAL_AGONIST','POSITIVE_ALLOSTERIC_MODULATOR','ACTIVATOR'].includes(edge.relation.toUpperCase())
  }
  const candidateEdges=(graphData?.edges??[]).filter(edge=>(relationFilter.length===0||relationFilter.includes(edge.relation))&&(edgeScope==='all'||(edgeScope==='direct_target'?isDirectDrugTarget(edge):!isDirectDrugTarget(edge))))
  const connectedNodeIds=new Set(candidateEdges.flatMap(edge=>[edge.source,edge.target]))
  const visibleNodes=(graphData?.nodes??[]).filter(node=>(nodeTypeFilter.length===0||nodeTypeFilter.includes(node.type))&&(edgeScope!=='direct_target'||node.id===centerNodeId||connectedNodeIds.has(node.id)))
  const visibleNodeIds=new Set(visibleNodes.map(node=>node.id))
  const visibleEdges=candidateEdges.filter(edge=>visibleNodeIds.has(edge.source)&&visibleNodeIds.has(edge.target))
  const baseHighlight=shortestLoadedPath(visibleEdges,pathStart,pathEnd)
  const highlighted=requestedPath?{nodeIds:new Set([...(requestedPath.nodes??[]).map((node:Record<string,any>)=>node.id),...baseHighlight.nodeIds]),edgeIds:new Set([...(requestedPath.edges??[]).map((edge:Record<string,any>)=>edge.edge_id),...baseHighlight.edgeIds])}:baseHighlight
  const elements=useMemo(()=>[
    ...visibleNodes.map(node=>({data:{id:node.id,label:node.label,type:node.type,detail:JSON.stringify(node.properties)},classes:[centerNodeId===node.id?'query-center':'',highlighted.nodeIds.has(node.id)?'path-highlight':''].filter(Boolean).join(' ')})),
    ...visibleEdges.map(edge=>({data:{id:edge.id,source:edge.source,target:edge.target,label:edge.relation,evidenceIds:edge.evidence_ids,directed:edge.directed!==false},classes:highlighted.edgeIds.has(edge.id)?'path-highlight':''})),
  ],[visibleNodes,visibleEdges,highlighted,centerNodeId])
  if(q.isLoading)return <Loading/>;if(q.error)return <Loading error={q.error as Error}/>
  const searchOptions=(suggestions.data?.items??[]).map(node=>({value:node.id,label:`${node.label}（${graphTypeLabel(node.type)}）`}))
  const exportGraph=()=>{const blob=new Blob([JSON.stringify({...graphData,nodes:visibleNodes,edges:visibleEdges},null,2)],{type:'application/json'});const anchor=document.createElement('a');anchor.href=URL.createObjectURL(blob);anchor.download='subgraph.json';anchor.click();URL.revokeObjectURL(anchor.href)}
  const nodeOptions=visibleNodes.map(node=>({value:node.id,label:`${node.label}（${graphTypeLabel(node.type)}）`}))
  const selectCenterNode=(id:string)=>{
    const chosen=suggestions.data?.items.find(node=>node.id===id)
    const scope=chosen?.type==='Drug'?'direct_target':'all'
    setCenterNodeId(id);setEdgeScope(scope);setCursor(0);setLoaded(null);setSelected(null);setPathStart(undefined);setPathEnd(undefined)
    setSearchParams(previous=>{const next=new URLSearchParams(previous);next.set('node_id',id);next.set('edge_scope',scope);if(searchTerm)next.set('q',searchTerm);else next.delete('q');if(activeBuildId)next.set('graph_build_id',activeBuildId);return next},{replace:true})
  }
  const clearCenterNode=()=>{
    setSearchText('');setSearchTerm('');setCenterNodeId(undefined);setCursor(0);setLoaded(null);setSelected(null);setPathStart(undefined);setPathEnd(undefined);setEdgeScope('all')
    setSearchParams(previous=>{const next=new URLSearchParams(previous);['node_id','q','edge_scope'].forEach(key=>next.delete(key));return next},{replace:true})
  }
  const selectBuild=(id:string)=>{
    setSelectedBuildId(id);setCursor(0);setLoaded(null);setCenterNodeId(undefined);setSearchText('');setSearchTerm('');setSelected(null)
    setSearchParams(previous=>{const next=new URLSearchParams(previous);next.set('graph_build_id',id);['node_id','q','edge_scope'].forEach(key=>next.delete(key));return next},{replace:true})
  }
  const updateEdgeScope=(scope:'all'|'direct_target'|'context')=>{
    setEdgeScope(scope)
    setSearchParams(previous=>{const next=new URLSearchParams(previous);next.set('edge_scope',scope);return next},{replace:true})
  }

  return <>
    {requestedPathId&&pathPackage.isLoading&&<Alert type="info" message="正在载入所选机制路径…"/>}
    {pathPackage.error&&<Alert type="error" message="路径证据包读取失败" description={(pathPackage.error as Error).message}/>}
    {requestedPathId&&pathPackage.data&&!requestedPath&&<Alert type="warning" message="所选 Path ID 不属于当前项目与图谱版本"/>}
    {requestedPath&&<Alert type="success" showIcon message={`正在高亮路径 ${requestedPathId} · ${requestedPath.route_type}`} description="节点和边来自当前项目指定 GraphBuild 的 KG06 证据包；点击边可查看 Evidence ID。"/>}

    <div className="page-heading">
      <div><Text className="eyebrow">机制探索 / 公共知识图谱</Text><Title level={2}>知识图谱全景</Title><Text type="secondary">未选择药物时展示当前图谱版本的全部节点和关系；缩放画布查看细节。选择节点后切换到该节点的局部证据子图，所选 KG06 路径会按原始 Path ID 高亮节点和边。</Text></div>
      <Button onClick={exportGraph} disabled={!graphData?.nodes.length}>导出当前筛选子图</Button>
    </div>

    <div className="graph-workspace">
      <Card className="section-card graph-controls">
        <Space wrap>
          <Input.Search value={searchText} placeholder="搜索药物、基因、通路或标准 ID" style={{width:320}} onChange={event=>setSearchText(event.target.value)} onSearch={setSearchTerm} enterButton="搜索"/>
          <Select showSearch optionFilterProp="label" placeholder={searchTerm.length<2?'输入至少 2 个字符后搜索':'选择搜索结果'} style={{width:350}} options={searchOptions} loading={suggestions.isFetching} value={centerNodeId} onChange={selectCenterNode}/>
          <Button onClick={clearCenterNode}>清除搜索</Button>
          <Select value={edgeScope} onChange={updateEdgeScope} style={{width:230}} options={[{value:'all',label:'全部证据关系'},{value:'direct_target',label:'直接药物—靶点关系'},{value:'context',label:'其他疾病/通路关系'}]}/>
          <Select mode="multiple" allowClear maxTagCount="responsive" placeholder="按节点类型筛选" style={{minWidth:210,maxWidth:360}} value={nodeTypeFilter} options={nodeTypes.map(type=>({value:type,label:graphTypeLabel(type)}))} onChange={setNodeTypeFilter}/>
          <Select mode="multiple" allowClear maxTagCount="responsive" placeholder="按关系类型筛选" style={{minWidth:210,maxWidth:360}} value={relationFilter} options={relationTypes.map(type=>({value:type,label:graphTypeLabel(type)}))} onChange={setRelationFilter}/>
          <Select showSearch optionFilterProp="label" allowClear placeholder="路径起点" style={{width:240}} value={pathStart} options={nodeOptions} onChange={setPathStart}/>
          <Select showSearch optionFilterProp="label" allowClear placeholder="路径终点" style={{width:240}} value={pathEnd} options={nodeOptions} onChange={setPathEnd}/>
        </Space>
        {pathStart&&pathEnd&&pathStart!==pathEnd&&highlighted.nodeIds.size===0&&<Alert type="warning" showIcon message="当前已加载的子图中未找到这两个节点之间的路径" style={{marginTop:12}}/>}
      </Card>
      <Card className="graph-card">{!graphData?.nodes.length?<Empty description={centerNodeId?'该节点在当前图谱版本中没有可显示的关联关系':'当前图谱版本没有可显示的关系'}/>:<GraphCanvas elements={elements} centerNodeId={centerNodeId} onSelect={setSelected} onEvidence={showGraphEvidence}/>}</Card>
      {centerNodeId&&edgeScope==='direct_target'&&visibleEdges.length===0&&<Alert type="info" showIcon message="该节点在当前版本中没有直接药物—靶点关系"/>}
      <Card title="节点详情" className="detail-card">{selected?<><Title level={5}>{selected.label}</Title><Tag>{graphTypeLabel(selected.type)}</Tag><Text code>{selected.id}</Text><pre>{JSON.stringify(selected.properties,null,2)}</pre></>:<Empty description="点击图中节点查看属性"/>}</Card>
    </div>
    <Card title="项目图谱构建" className="section-card">
      <Space direction="vertical" style={{width:'100%'}}>
        <Alert type="info" showIcon message="生成可追溯的项目 GraphBundle" description="只使用同一项目中已完成且相互关联的 S1、S2 和通路富集运行；药物按 InChIKey 精确映射，剂量和时间条件分别保留。"/>
        {runs.error&&<Alert type="error" showIcon message="分析运行列表读取失败" description={(runs.error as Error).message}/>}
        {!runs.isLoading&&!runs.error&&!bundleS1&&<Alert type="warning" showIcon message="当前项目没有已完成的 S1 运行，暂不能生成 GraphBundle"/>}
        {!runs.isLoading&&!runs.error&&bundleS1&&(!bundleS2||!bundleEnrichment)&&<Alert type="warning" showIcon message="缺少与所选 S1 匹配的 S2 或通路富集运行" description="请先在 S2 与 S1 通路分析页完成对应运行；只有基于同一个 S1 的结果才能组装 GraphBundle。"/>}
        <Space wrap>
          <Select style={{width:300}} placeholder="选择已完成的 S1 运行" value={bundleS1} options={(runs.data??[]).filter(run=>['s1_precomputed_deg','s1_limma_microarray','s1_rnaseq_edger_voom'].includes(run.run_type)&&run.status==='completed').map(run=>({value:run.analysis_run_id,label:`${runTypeLabel(run.run_type)} · ${run.analysis_run_id}`}))} onChange={setBundleS1}/>
          <Select style={{width:300}} placeholder="选择关联的 S2 运行" value={bundleS2} options={(runs.data??[]).filter(run=>run.run_type==='s2_lincs'&&run.status==='completed').map(run=>({value:run.analysis_run_id,label:`${runTypeLabel(run.run_type)} · ${run.analysis_run_id}`}))} onChange={setBundleS2}/>
          <Select style={{width:300}} placeholder="选择关联的富集运行" value={bundleEnrichment} options={(runs.data??[]).filter(run=>run.run_type==='s1_pathway_enrichment'&&run.status==='completed').map(run=>({value:run.analysis_run_id,label:`${runTypeLabel(run.run_type)} · ${run.analysis_run_id}`}))} onChange={setBundleEnrichment}/>
          <Button type="primary" disabled={!bundleS1||!bundleS2||!bundleEnrichment} loading={createBundle.isPending} onClick={()=>createBundle.mutate()}>生成并构建图谱</Button>
          <Button disabled={!latestBundleId||createBundle.isPending} loading={importBundle.isPending} onClick={()=>importBundle.mutate(latestBundleId)}>导入已有最新 GraphBundle</Button>
        </Space>
        <Text type="secondary">已生成 {graphBundleRuns.length} 个版本化 GraphBundle；点击“生成并构建图谱”会在 GraphBundle 校验通过后继续导入 Neo4j、创建 GraphBuild，并自动切换到新版本。</Text>
      </Space>
    </Card>

    <Card title="图谱版本记录" className="section-card">
      <Space direction="vertical" style={{width:'100%'}}>
        <Alert type="info" showIcon message="图谱版本登记与 Neo4j 数据关联" description="操作会校验输入 SHA-256，并将图谱关系幂等导入、标记所属版本；不删除已有版本。"/>
        <Space wrap>
          <Select style={{minWidth:340}} value={activeBuildId} placeholder="选择图谱版本" options={queryableBuilds.map(build=>({value:build.graph_build_id,label:`${build.graph_build_id} · ${statusLabel(build.status)}`}))} onChange={selectBuild}/>
          <Button type="primary" loading={registerBuild.isPending} onClick={()=>registerBuild.mutate()}>登记当前快照</Button>
          <Text type="secondary">已登记 {builds.data?.items.length??0} 个版本，其中 {queryableBuilds.length} 个可查询</Text>
        </Space>
        <Text type="secondary">当前选中版本实时统计：{activeGraphSummary.data?`${activeGraphSummary.data.node_count} 个节点、${activeGraphSummary.data.edge_count} 条关系`:activeGraphSummary.isLoading?"读取中":"不可用"}</Text>
        {builds.error&&<Alert type="error" message="版本记录读取失败" description={(builds.error as Error).message}/>}
        {(builds.data?.items??[]).map(build=><Card size="small" key={build.graph_build_id}><Space direction="vertical"><Text code>{build.graph_build_id}</Text><Text type="secondary">状态：{build.status==='materialized'?'已导入 Neo4j 并按版本标记':build.status==='failed'?'导入失败':'待 Neo4j 版本标记'} · 来源：{build.graph_source} · 关联运行：{build.analysis_run_id}</Text><Text type="secondary">输入文件：{Object.keys(build.input_hashes).length} 项 · 登记时节点 {String(build.summary.node_count??'—')} · 登记时关系 {String(build.summary.edge_count??'—')}</Text></Space></Card>)}
      </Space>
    </Card>

    <Alert type="warning" showIcon message="解读限制" description="知识图谱关系表示可追溯的数据库断言与项目表达证据交集，不代表药物疗效。"/>
    <Modal title={selectedGraphEdge?`关系详情 · ${graphTypeLabel(selectedGraphEdge.relation)}`:'关系详情'} open={!!selectedGraphEdge} onCancel={()=>{setSelectedGraphEdge(null);setSelectedEvidenceId(undefined)}} footer={null} width={760}>
      <Space direction="vertical" style={{width:'100%'}}>
        <Text>关系类型：{selectedGraphEdge?.relation}</Text>
        <Text>起点：<Text code>{selectedGraphEdge?.source}</Text></Text>
        <Text>终点：<Text code>{selectedGraphEdge?.target}</Text></Text>
        <Text>Evidence ID：{selectedGraphEdge?.evidence_ids.length?selectedGraphEdge.evidence_ids.join(', '):'当前记录未附 Evidence ID'}</Text>
        {selectedEvidenceId&&graphEvidence.isLoading?<Spin/>:selectedEvidenceId&&graphEvidence.error?<Alert type="error" message="来源证据读取失败" description={(graphEvidence.error as Error).message}/>:selectedEvidenceId?<pre style={{maxHeight:400,overflow:'auto',whiteSpace:'pre-wrap'}}>{JSON.stringify(graphEvidence.data,null,2)}</pre>:<Text type="secondary">此关系没有可解析的独立证据记录。</Text>}
      </Space>
    </Modal>
  </>
}
