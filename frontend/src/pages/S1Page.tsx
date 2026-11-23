import { lazy, Suspense, useEffect, useState } from 'react'
import { Alert, Button, Card, Empty, Input, InputNumber, Select, Space, Spin, Statistic, Table, Tag, Typography, message } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, PathwayCollection, PathwayItem, S1Gene, VolcanoPoint } from '../api'
import { Loading, useProject } from '../projectContext'
import { contrastLabel, identifierLabel, runTypeLabel, statusLabel } from '../locales/zh-CN'
import { palette } from '../designTokens'

const { Title, Text } = Typography
const ReactECharts = lazy(() => import('../ChartRenderer'))

function PathwayChart({ title, items, collection }: { title: string; items: PathwayItem[]; collection: PathwayCollection }) {
  const isHallmark = collection === 'hallmark_gsea'
  const rows = [...items].sort((a, b) => isHallmark ? Math.abs(Number(b.NES ?? 0)) - Math.abs(Number(a.NES ?? 0)) : Number(a['p.adjust'] ?? a.padj ?? 1) - Number(b['p.adjust'] ?? b.padj ?? 1)).slice(0, 10)
  const categories = rows.map((r) => String(r.Description ?? r.pathway ?? r.ID ?? ''))
  const values = rows.map((r) => isHallmark ? Number(r.NES ?? 0) : -Math.log10(Math.max(Number(r['p.adjust'] ?? r.padj ?? 1), 1e-300)))
  return <Card title={title} className="section-card"><Suspense fallback={<div style={{height:320,display:'grid',placeItems:'center',color:palette.subtle}}>正在加载图表…</div>}><ReactECharts style={{height: 320}} option={{tooltip:{trigger:'axis',formatter:(p:{name:string;value:number}[])=>`${p[0]?.name}<br/>${isHallmark?'NES':'−log10(FDR)'}: ${Number(p[0]?.value).toFixed(2)}`},grid:{left:150,right:24,top:12,bottom:30},xAxis:{type:'value',name:isHallmark?'NES':'−log10(FDR)'},yAxis:{type:'category',data:categories,inverse:true,axisLabel:{width:140,overflow:'truncate'}},series:[{type:'bar',data:values,itemStyle:{color:(p:{value:number})=>isHallmark?(p.value>=0?palette.up:palette.down):palette.success}}]}} /></Suspense></Card>
}

function VolcanoChart({ points, threshold, contrast }: { points: VolcanoPoint[]; threshold: number; contrast: string }) {
  const groups = [
    {name:'显著上调',key:'up',color:palette.up},
    {name:'显著下调',key:'down',color:palette.down},
    {name:'未达 FDR 0.05',key:'not_significant',color:palette.neutral},
  ] as const
  const series = groups.map(group=>({
    name:group.name,
    type:'scatter' as const,
    symbolSize:5,
    large:true,
    largeThreshold:2000,
    itemStyle:{color:group.color,opacity:group.key==='not_significant'?0.38:0.78},
    data:points.filter(point=>point.direction===group.key).map(point=>[point.logFC,point.minus_log10_fdr,point.gene_symbol,point['adj.P.Val']]),
  }))
  return <Suspense fallback={<div style={{height:440,display:'grid',placeItems:'center',color:palette.subtle}}>正在加载火山图…</div>}><ReactECharts style={{height:440}} option={{
    animation:false,
    legend:{top:0},
    tooltip:{trigger:'item',formatter:(params:{seriesName:string;value:[number,number,string,number]})=>`${params.value[2]}<br/>${params.seriesName}<br/>logFC: ${params.value[0].toFixed(3)}<br/>FDR: ${Number(params.value[3]).toExponential(2)}`},
    grid:{left:64,right:24,top:44,bottom:52},
    xAxis:{type:'value',name:`logFC（${contrast}）`,nameLocation:'middle',nameGap:32,splitLine:{lineStyle:{color:palette.grid}}},
    yAxis:{type:'value',name:'−log10(FDR)',nameLocation:'middle',nameGap:46,splitLine:{lineStyle:{color:palette.grid}}},
    series:[...series,{name:'FDR = 0.05',type:'line' as const,symbol:'none',silent:true,lineStyle:{color:palette.threshold,type:'dashed',width:1},data:[[-100,threshold],[100,threshold]]}],
  }} /></Suspense>
}

function LimmaMatrixForm({projectId,datasets}:{projectId:string;datasets:Array<{dataset_id:string;state:string;filename?:string|null;validation:Record<string,unknown>}>}) {
  const [matrixId,setMatrixId]=useState<string>()
  const [metadataId,setMetadataId]=useState<string>()
  const [positive,setPositive]=useState('Tumor')
  const [negative,setNegative]=useState('Normal')
  const [identifierType,setIdentifierType]=useState<'symbol'|'entrez'|'ensembl'>('symbol')
  const [fdr,setFdr]=useState(0.05)
  const queryClient=useQueryClient()
  const matrices=datasets.filter(item=>item.validation.dataset_type==='expression_matrix')
  const annotations=datasets.filter(item=>item.validation.dataset_type==='sample_metadata')
  const run=useMutation({mutationFn:()=>{if(!matrixId||!metadataId)throw new Error('请选择表达矩阵和样本注释');return api.runLimmaS1(projectId,matrixId,{sample_metadata_dataset_id:metadataId,positive_group:positive,negative_group:negative,identifier_type:identifierType,fdr_threshold:fdr,measurement_type:'normalized_log2_microarray'})},onSuccess:async(result)=>{message.success(`limma S1 已完成：${result.analysis_run_id}`);await Promise.all([queryClient.invalidateQueries({queryKey:['s1',projectId]}),queryClient.invalidateQueries({queryKey:['s1-genes',projectId]}),queryClient.invalidateQueries({queryKey:['s1-volcano',projectId]}),queryClient.invalidateQueries({queryKey:['datasets',projectId]})])},onError:(error:Error)=>message.error(`limma S1 运行失败：${error.message}`)})
  return <Card title="从表达矩阵运行 S1（limma）" className="section-card"><Alert type="info" showIcon message="仅用于 log2 标准化的连续型微阵列表达值" description="本流程不接受 RNA-seq 原始 counts；需要完全匹配的样本 ID、每组至少 2 个样本，并明确指定正向组减负向组。" style={{marginBottom:12}}/><Space wrap><Select style={{minWidth:260}} value={matrixId} placeholder="选择表达矩阵" options={matrices.map(item=>({value:item.dataset_id,label:`${item.filename??item.dataset_id} · ${statusLabel(item.state)}`}))} onChange={setMatrixId}/><Select style={{minWidth:250}} value={metadataId} placeholder="选择样本分组注释" options={annotations.map(item=>({value:item.dataset_id,label:`${item.filename??item.dataset_id} · ${statusLabel(item.state)}`}))} onChange={setMetadataId}/><Input value={positive} onChange={event=>setPositive(event.target.value)} addonBefore="正向组" style={{width:230}}/><Input value={negative} onChange={event=>setNegative(event.target.value)} addonBefore="负向组" style={{width:230}}/><Select value={identifierType} onChange={setIdentifierType} options={[{value:'symbol',label:identifierLabel('symbol')},{value:'entrez',label:identifierLabel('entrez')},{value:'ensembl',label:identifierLabel('ensembl')}]}/><InputNumber min={0.000001} max={1} step={0.01} value={fdr} onChange={value=>setFdr(Number(value??0.05))} addonBefore="FDR"/><Button type="primary" loading={run.isPending} disabled={!matrixId||!metadataId||!positive.trim()||!negative.trim()||positive.trim()===negative.trim()} onClick={()=>run.mutate()}>运行 limma</Button></Space>{(!matrices.length||!annotations.length)&&<Text type="secondary" style={{display:'block',marginTop:10}}>请先上传表达矩阵和样本分组注释；两种数据都需通过结构校验。</Text>}</Card>
}

function RNASeqCountsForm({projectId,datasets}:{projectId:string;datasets:Array<{dataset_id:string;state:string;filename?:string|null;validation:Record<string,unknown>}>}) {
  const [countsId,setCountsId]=useState<string>()
  const [metadataId,setMetadataId]=useState<string>()
  const [positive,setPositive]=useState('Case')
  const [negative,setNegative]=useState('Control')
  const [identifierType,setIdentifierType]=useState<'symbol'|'entrez'|'ensembl'>('symbol')
  const [fdr,setFdr]=useState(0.05)
  const queryClient=useQueryClient()
  const matrices=datasets.filter(item=>item.validation.dataset_type==='expression_matrix')
  const annotations=datasets.filter(item=>item.validation.dataset_type==='sample_metadata')
  const run=useMutation({mutationFn:()=>{if(!countsId||!metadataId)throw new Error('请选择原始 counts 矩阵和样本注释');return api.runRNASeqS1(projectId,countsId,{sample_metadata_dataset_id:metadataId,positive_group:positive,negative_group:negative,identifier_type:identifierType,fdr_threshold:fdr,measurement_type:'raw_integer_counts'})},onSuccess:async(result)=>{message.success(`RNA-seq S1 已完成：${result.analysis_run_id}`);await Promise.all([queryClient.invalidateQueries({queryKey:['s1',projectId]}),queryClient.invalidateQueries({queryKey:['s1-genes',projectId]}),queryClient.invalidateQueries({queryKey:['s1-volcano',projectId]}),queryClient.invalidateQueries({queryKey:['datasets',projectId]})])},onError:(error:Error)=>message.error(`RNA-seq S1 运行失败：${error.message}`)})
  return <Card title="从 RNA-seq 原始 counts 运行 S1（edgeR + limma-voom）" className="section-card"><Alert type="warning" showIcon message="仅接受原始非负整数 counts" description="分析依次执行 filterByExpr、TMM 标准化和 voom；TPM/FPKM/CPM、估计表达值和已标准化矩阵会被拒绝。样本 ID 必须完全匹配且每组至少 2 个样本。" style={{marginBottom:12}}/><Space wrap><Select style={{minWidth:260}} value={countsId} placeholder="选择 RNA-seq counts 矩阵" options={matrices.map(item=>({value:item.dataset_id,label:`${item.filename??item.dataset_id} · ${statusLabel(item.state)}`}))} onChange={setCountsId}/><Select style={{minWidth:250}} value={metadataId} placeholder="选择样本分组注释" options={annotations.map(item=>({value:item.dataset_id,label:`${item.filename??item.dataset_id} · ${statusLabel(item.state)}`}))} onChange={setMetadataId}/><Input value={positive} onChange={event=>setPositive(event.target.value)} addonBefore="正向组" style={{width:220}}/><Input value={negative} onChange={event=>setNegative(event.target.value)} addonBefore="负向组" style={{width:220}}/><Select value={identifierType} onChange={setIdentifierType} options={[{value:'symbol',label:identifierLabel('symbol')},{value:'entrez',label:identifierLabel('entrez')},{value:'ensembl',label:identifierLabel('ensembl')}]}/><InputNumber min={0.000001} max={1} step={0.01} value={fdr} onChange={value=>setFdr(Number(value??0.05))} addonBefore="FDR"/><Button type="primary" loading={run.isPending} disabled={!countsId||!metadataId||!positive.trim()||!negative.trim()||positive.trim()===negative.trim()} onClick={()=>run.mutate()}>运行 RNA-seq</Button></Space>{(!matrices.length||!annotations.length)&&<Text type="secondary" style={{display:'block',marginTop:10}}>请先上传 counts 矩阵和样本分组注释；两种数据都需通过结构校验。</Text>}</Card>
}

function S1EnrichmentForm({projectId}:{projectId:string}) {
  const runs=useQuery({queryKey:['project-runs',projectId],queryFn:()=>api.runs(projectId)})
  const s1Runs=(runs.data??[]).filter(run=>run.status==='completed'&&['s1_precomputed_deg','s1_limma_microarray','s1_rnaseq_edger_voom'].includes(run.run_type))
  const [s1RunId,setS1RunId]=useState<string>()
  const [identifierType,setIdentifierType]=useState<'symbol'|'entrez'|'ensembl'>('symbol')
  const [fdr,setFdr]=useState(0.05)
  const client=useQueryClient()
  useEffect(()=>{if(!s1RunId&&s1Runs[0])setS1RunId(s1Runs[0].analysis_run_id)},[s1Runs,s1RunId])
  const run=useMutation({mutationFn:()=>{if(!s1RunId)throw new Error('请选择本项目已完成的 S1 运行');return api.runPathwayEnrichment(projectId,{s1_analysis_run_id:s1RunId,identifier_type:identifierType,fdr_threshold:fdr})},onSuccess:async result=>{message.success(`通路富集完成：${result.analysis_run_id}`);await Promise.all([client.invalidateQueries({queryKey:['s1',projectId]}),client.invalidateQueries({queryKey:['project-runs',projectId]}),client.invalidateQueries({queryKey:['pathways',projectId]})])},onError:(error:Error)=>message.error(`通路富集失败：${error.message}`)})
  return <Card title="运行项目级 S1 通路富集" className="section-card"><Alert type="info" showIcon message="使用所选 S1 运行独立生成 GO BP、Reactome 和 Hallmark 结果" description="ORA 背景采用该 S1 已检验且成功映射的基因；Hallmark 使用全体可映射的带符号 t 统计量。新结果保存在独立 AnalysisRun 中，不覆盖 S1 表。" style={{marginBottom:12}}/><Space wrap><Select style={{minWidth:420}} value={s1RunId} placeholder="选择已完成的 S1 运行" loading={runs.isLoading} options={s1Runs.map(item=>({value:item.analysis_run_id,label:`${runTypeLabel(item.run_type)} · ${item.analysis_run_id}`}))} onChange={setS1RunId}/><Select value={identifierType} onChange={setIdentifierType} options={[{value:'symbol',label:identifierLabel('symbol')},{value:'entrez',label:identifierLabel('entrez')},{value:'ensembl',label:identifierLabel('ensembl')}]}/><InputNumber min={0.000001} max={1} step={0.01} value={fdr} onChange={value=>setFdr(Number(value??0.05))} addonBefore="FDR"/><Button type="primary" loading={run.isPending} disabled={!s1RunId} onClick={()=>run.mutate()}>运行富集分析</Button></Space>{!s1Runs.length&&<Text type="secondary" style={{display:'block',marginTop:10}}>该项目还没有完成的 S1 运行。</Text>}</Card>
}

export default function S1Page() {
  const { project, isLoading: projectLoading, error: projectError } = useProject(); const q = useQuery({ queryKey: ['s1', project?.project_id], queryFn: () => api.s1(project!.project_id), enabled: !!project })
  const [externalPage,setExternalPage]=useState(1)
  const externalValidation=useQuery({queryKey:['s1-external-validation',project?.project_id,externalPage],queryFn:()=>api.s1ExternalValidation(project!.project_id,(externalPage-1)*20,20),enabled:project?.slug==='erpos-gse42568'})
  const datasets=useQuery({queryKey:['datasets',project?.project_id],queryFn:()=>api.datasets(project!.project_id),enabled:!!project})
  const [s1DatasetId,setS1DatasetId]=useState<string>()
  const [positiveGroup,setPositiveGroup]=useState('Case')
  const [negativeGroup,setNegativeGroup]=useState('Control')
  const [fdrThreshold,setFdrThreshold]=useState(0.05)
  const queryClient=useQueryClient()
  const runS1=useMutation({mutationFn:()=>{if(!project||!s1DatasetId)throw new Error('请选择预计算差异表达数据');return api.runPrecomputedS1(project.project_id,s1DatasetId,{positive_group:positiveGroup,negative_group:negativeGroup,fdr_threshold:fdrThreshold})},onSuccess:async(result)=>{message.success(`S1 已完成：${result.analysis_run_id}`);await Promise.all([queryClient.invalidateQueries({queryKey:['s1',project?.project_id]}),queryClient.invalidateQueries({queryKey:['s1-genes',project?.project_id]}),queryClient.invalidateQueries({queryKey:['s1-volcano',project?.project_id]}),queryClient.invalidateQueries({queryKey:['datasets',project?.project_id]})])},onError:(error:Error)=>message.error(`S1 运行失败：${error.message}`)})
  const [geneDirection,setGeneDirection]=useState<'all'|'up'|'down'>('all')
  const [genePage,setGenePage]=useState(1)
  const genes=useQuery({queryKey:['s1-genes',project?.project_id,geneDirection,genePage],queryFn:()=>api.s1Genes(project!.project_id,geneDirection,genePage),enabled:!!project})
  const volcano=useQuery({queryKey:['s1-volcano',project?.project_id],queryFn:()=>api.s1Volcano(project!.project_id),enabled:!!project})
  useEffect(()=>setGenePage(1),[project?.project_id,geneDirection])
  const collections: PathwayCollection[] = ['go_up','go_down','reactome_up','reactome_down','hallmark_gsea']
  const goUp = useQuery({queryKey:['pathways',project?.project_id,'go_up'],queryFn:()=>api.pathways(project!.project_id,'go_up'),enabled:!!project})
  const goDown = useQuery({queryKey:['pathways',project?.project_id,'go_down'],queryFn:()=>api.pathways(project!.project_id,'go_down'),enabled:!!project})
  const reactomeUp = useQuery({queryKey:['pathways',project?.project_id,'reactome_up'],queryFn:()=>api.pathways(project!.project_id,'reactome_up'),enabled:!!project})
  const reactomeDown = useQuery({queryKey:['pathways',project?.project_id,'reactome_down'],queryFn:()=>api.pathways(project!.project_id,'reactome_down'),enabled:!!project})
  const hallmark = useQuery({queryKey:['pathways',project?.project_id,'hallmark_gsea'],queryFn:()=>api.pathways(project!.project_id,'hallmark_gsea'),enabled:!!project})
  const pathways = [goUp,goDown,reactomeUp,reactomeDown,hallmark]
  if (projectLoading) return <Loading />; if (projectError) return <Loading error={projectError as Error} />; if (!project) return <Empty description="暂无项目" />; if (q.isLoading||volcano.isLoading) return <Loading />; if (q.error) return <Loading error={q.error as Error} />; if (volcano.error) return <Loading error={volcano.error as Error} />
  const d = q.data!
  const pathwayTitles = ['GO BP · 上调基因','GO BP · 下调基因','Reactome · 上调基因','Reactome · 下调基因','Hallmark GSEA · 正负 NES']
  const geneColumns=[
    {title:'基因标识',dataIndex:'gene_symbol',width:180,render:(value:string)=><Text code>{value}</Text>},
    {title:'方向',dataIndex:'direction',width:90,render:(value:string)=><Tag color={value==='up'?'volcano':'blue'}>{value==='up'?'上调':'下调'}</Tag>},
    {title:'logFC',dataIndex:'logFC',width:120,render:(value:number)=>value.toFixed(4)},
    {title:'t 统计量',dataIndex:'t',width:120,render:(value:number)=>value.toFixed(3)},
    {title:'adj.P.Val',dataIndex:'adj.P.Val',width:150,render:(value:number)=><Text>{value.toExponential(3)}</Text>},
  ]
  const threshold=Number(d.fdr_threshold??0.05)
  const precomputedDatasets=(datasets.data?.items??[]).filter(item=>item.validation.dataset_type==='precomputed_deg')
  const externalSummary=externalValidation.data?.summary??{}
  const externalColumns=[{title:'外部名次',dataIndex:'external_rank'},{title:'pert_id / 药物',dataIndex:'drug_name',render:(name:string,row:{pert_id:string})=><><Text code>{row.pert_id}</Text><br/>{name}</>},{title:'剂量 / 时间',render:(_:unknown,row:{dose:string;time:string})=>`${row.dose} / ${row.time}`},{title:'外部 WTCS',dataIndex:'WTCS_median',render:(value:number|null)=>value==null?'—':value.toFixed(4)},{title:'发现队列 B200 名次',dataIndex:'B200_rank'},{title:'发现队列 WTCS',dataIndex:'B200_WTCS_median',render:(value:number|null)=>value==null?'—':value.toFixed(4)}]
  return <><div className="page-heading"><div><Text className="eyebrow">分析结果 / S1</Text><Title level={2}>疾病表达特征</Title><Text type="secondary">{contrastLabel(typeof d.contrast==='string'?d.contrast:undefined)} · {String(d.source??'等待 S1 结果')}</Text></div></div>{project.slug!=='erpos-gse42568'&&<RNASeqCountsForm projectId={project.project_id} datasets={datasets.data?.items??[]} />}{project.slug!=='erpos-gse42568'&&<LimmaMatrixForm projectId={project.project_id} datasets={datasets.data?.items??[]} />}{project.slug!=='erpos-gse42568'&&<Card title="运行项目级 S1（预计算差异表）" className="section-card"><Alert type="info" showIcon message="该流程只接收已计算的差异表达表" description="指定 logFC 正方向对应的组别；系统保留输入统计量、按基因 ID 去重并记录输入输出 SHA-256。表达矩阵尚需样本分组配置和 limma 适配器。" style={{marginBottom:12}}/><Space wrap><Select style={{minWidth:280}} value={s1DatasetId} placeholder="选择已上传的预计算 DEG 表" options={precomputedDatasets.map(item=>({value:item.dataset_id,label:`${item.filename??item.dataset_id} · ${statusLabel(item.state)}`}))} onChange={setS1DatasetId}/><Input value={positiveGroup} onChange={event=>setPositiveGroup(event.target.value)} addonBefore="logFC 正向组" style={{width:260}}/><Input value={negativeGroup} onChange={event=>setNegativeGroup(event.target.value)} addonBefore="logFC 负向组" style={{width:250}}/><InputNumber min={0.000001} max={1} step={0.01} value={fdrThreshold} onChange={value=>setFdrThreshold(Number(value??0.05))} addonBefore="FDR"/><Button type="primary" loading={runS1.isPending} disabled={!s1DatasetId||!positiveGroup.trim()||!negativeGroup.trim()||positiveGroup.trim()===negativeGroup.trim()} onClick={()=>runS1.mutate()}>运行 S1</Button></Space>{!precomputedDatasets.length&&<Text type="secondary" style={{display:'block',marginTop:10}}>请先在右上角上传数据，类型选择“已计算差异表达结果”。</Text>}</Card>}{project.slug!=='erpos-gse42568'&&<S1EnrichmentForm projectId={project.project_id}/ >}{d.available===false&&<Alert type="info" showIcon message="该项目尚无 S1 分析结果" description="新项目不会沿用 ER 阳性乳腺癌项目的差异表达数据。"/>}<div className="stats-grid"><Card><Statistic title="分析基因" value={d.tested_genes as number} /></Card><Card><Statistic title={`FDR < ${threshold}`} value={(d.significant_genes as number|undefined)??(d.significant_genes_fdr05 as number)} /></Card><Card><Statistic title="上调" value={d.up as number} /></Card><Card><Statistic title="下调" value={d.down as number} /></Card></div>{project.slug==='erpos-gse42568'&&<Card title="独立队列验证 · GSE139038（Exp010）" className="section-card">{externalValidation.isLoading?<Spin/>:externalValidation.error?<Alert type="error" message="外部验证结果读取失败" description={(externalValidation.error as Error).message}/>:externalValidation.data?.available?<><Alert type="warning" showIcon message="小样本外部复核，不构成临床疗效证据" description={`严格配对 ${String(externalValidation.data.sample_design.paired_ER_positive_patients)} 名 ER 阳性患者；发现队列和外部队列样本无重叠。外部 S1 的 LINCS WTCS 排名按剂量/时间分层，不能解释为药物疗效排序。Exp010 manifest、摘要和排名文件均通过 SHA-256 核验。`}/><div className="stats-grid"><Card><Statistic title="共同检测基因" value={Number(externalSummary.n_common_genes??0)} /></Card><Card><Statistic title="全体基因方向一致率" value={`${(Number(externalSummary.overall_direction_concordance??0)*100).toFixed(1)}%`} /></Card><Card><Statistic title="两队列显著基因方向一致率" value={`${(Number(externalSummary.both_significant_direction_concordance??0)*100).toFixed(1)}%`} /></Card><Card><Statistic title="WTCS 排名 Spearman" value={Number(externalSummary.ranking_spearman??0).toFixed(3)} /></Card></div><Table rowKey={(row:{pert_id:string;dose:string;time:string})=>`${row.pert_id}|${row.dose}|${row.time}`} size="small" dataSource={externalValidation.data.items} columns={externalColumns} loading={externalValidation.isFetching} pagination={{current:externalPage,pageSize:20,total:externalValidation.data.total_conditions,onChange:setExternalPage,showSizeChanger:false}}/><Text type="secondary">外部查询：{String(externalSummary.external_query_up_n)} UP / {String(externalSummary.external_query_down_n)} DOWN；共同条件 {String(externalSummary.ranking_common_conditions)}；Top10 重合药物 ID {String(externalSummary.top10_overlap_unique_pert_id)}。结果来源：{externalValidation.data.provenance.selection} · manifest SHA-256 {externalValidation.data.provenance.manifest_sha256?.slice(0,12)}…</Text></>:<Alert type="info" message={externalValidation.data?.reason??'该项目无外部验证数据'} />}</Card>}<Card title="全量差异表达火山图" className="section-card"><Alert type="info" showIcon message={`方向为 ${contrastLabel(typeof d.contrast==='string'?d.contrast:undefined)}`} description={`横轴为 logFC，纵轴为 −log10(FDR)；颜色使用 FDR < ${threshold} 判定上调、下调或未显著。`} style={{marginBottom:12}}/><VolcanoChart points={volcano.data?.points??[]} threshold={-Math.log10(Number(volcano.data?.fdr_threshold??threshold))} contrast={contrastLabel(typeof d.contrast==='string'?d.contrast:undefined)} /></Card><Card title="显著差异基因" className="section-card"><Space style={{marginBottom:12}}><Text>显示方向</Text><Select<'all'|'up'|'down'> value={geneDirection} onChange={value=>{setGeneDirection(value);setGenePage(1)}} options={[{value:'all',label:`全部显著（${Number(d.significant_genes??d.significant_genes_fdr05).toLocaleString()}）`},{value:'up',label:`上调（${Number(d.up).toLocaleString()}）`},{value:'down',label:`下调（${Number(d.down).toLocaleString()}）`}]}/></Space>{genes.error?<Alert type="error" message={(genes.error as Error).message}/>:<Table<S1Gene> rowKey="gene_symbol" size="small" loading={genes.isLoading} dataSource={genes.data?.items??[]} columns={geneColumns} pagination={{current:genePage,pageSize:20,total:genes.data?.total,onChange:setGenePage,showSizeChanger:false}} />}</Card>{d.pathway_enrichment_available===true?<><Alert type="success" showIcon message="S1 通路富集结果已接入" description={`使用实际 S1 全量 limma 的通路分析结果。映射背景 ${String(d.pathway_gene_universe)} 个 Entrez 基因；GO BP 显著项：上调 ${String((d.pathway_counts as Record<string,number>)?.go_up)}、下调 ${String((d.pathway_counts as Record<string,number>)?.go_down)}；Hallmark 显著集 ${String((d.pathway_counts as Record<string,number>)?.hallmark_gsea)}。`} />{pathways.map((result,i)=>result.isLoading?<Spin key={collections[i]} />:result.error?<Alert key={collections[i]} type="error" message={`通路数据读取失败：${collections[i]}`} />:<PathwayChart key={collections[i]} title={pathwayTitles[i]} collection={collections[i]} items={result.data?.items??[]} />)}</>:<Alert type="info" showIcon message="通路富集结果未接入" description="当前项目没有可读取的 GO、Reactome 或 Hallmark 分析结果。" />}</>
}
