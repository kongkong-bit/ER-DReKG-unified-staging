import { useEffect, useState } from 'react'
import { Alert, Button, Card, Input, InputNumber, Select, Space, Table, Tag, Typography, message, Modal } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import { Loading, useProject } from '../projectContext'
import { identifierLabel, mappingStatusLabel, runTypeLabel } from '../locales/zh-CN'

const { Title, Text } = Typography

export default function S2Page() {
  const { project } = useProject(); const [offset,setOffset] = useState(0); const q = useQuery({ queryKey: ['candidate-evidence', project?.project_id, offset], queryFn: () => api.candidateEvidence(project!.project_id,offset,10), enabled: !!project })
  const projectS2=useQuery({queryKey:['project-s2-summary',project?.project_id],queryFn:()=>api.s2Summary(project!.project_id),enabled:!!project})
  const conditions=useQuery({queryKey:['project-s2-conditions',project?.project_id,offset],queryFn:()=>api.s2Conditions(project!.project_id,offset,10),enabled:!!project})
  const stability=useQuery({queryKey:['project-s2-stability',project?.project_id],queryFn:()=>api.s2Stability(project!.project_id),enabled:!!project})
  if (q.isLoading) return <Loading />; if (q.error) return <Loading error={q.error as Error} />
  const columns = [
    {title:'Exp006 原排名',dataIndex:'rank',width:110,fixed:'left' as const},
    {title:'药物',dataIndex:'drug_name',width:150,fixed:'left' as const},
    {title:'LINCS ID',dataIndex:'pert_id',width:150,render:(x:string)=><Text code>{x}</Text>},
    {title:'图谱映射状态',dataIndex:'kg_mapping_status',width:230,render:(value:string)=><Tag title={value} color={value?.includes('with_supported_path')?'green':value?.includes('no_exact')?'orange':'default'}>{mappingStatusLabel(value)||'未评估'}</Tag>},
    {title:'图谱交汇路径',dataIndex:'kg_supported_route_count',width:120},
    {title:'图谱靶基因',dataIndex:'kg_unique_target_gene_count',width:100},
    {title:'图谱通路',dataIndex:'kg_unique_pathway_count',width:90},
    {title:'项目 S2 条件',dataIndex:'project_s2_condition_count',width:100},
    {title:'项目 S2 剂量',dataIndex:'project_s2_distinct_doses',width:260},
    {title:'WTCS 中位数（B）',dataIndex:'wtcs_median_B',width:145,render:(x:string)=><Text code>{x||'—'}</Text>},
    {title:'签名数',dataIndex:'n_signatures',width:90},
    {title:'稳定性',dataIndex:'stability_grade',width:100,render:(x:string)=><Tag color={x==='low'?'orange':'blue'}>{mappingStatusLabel(x)||'—'}</Tag>},
    {title:'外部 S1 中位排名',dataIndex:'external_s1_median_rank',width:150,render:(x:string)=><Text>{x||'—'}</Text>},
    {title:'ER+ 平均敏感性',dataIndex:'erpos_mean_sensitivity',width:140,render:(x:string)=><Text>{x||'—'}</Text>},
    {title:'ER− 平均敏感性',dataIndex:'erneg_mean_sensitivity',width:140,render:(x:string)=><Text>{x||'—'}</Text>},
    {title:'PRISM 说明',dataIndex:'PRISM_endpoint',width:280,render:(x:string)=><Text type="secondary">{x||'—'}</Text>},
    {title:'限制',dataIndex:'evidence_limitations',width:200,render:(x:string)=><Text type="secondary">{x||'—'}</Text>},
  ]
  const projectRunForm = project && project.slug !== 'erpos-gse42568' ? <ProjectS2RunForm projectId={project.project_id} projectStatus={project.status} /> : null
  if(q.data?.available===false&&projectS2.data?.available){
    const conditionColumns=[{title:'药物',dataIndex:'drug_name',width:160},{title:'LINCS ID',dataIndex:'pert_id',width:180,render:(value:string)=><Text code>{value}</Text>},{title:'细胞/扰动',render:(_:unknown,row:{cell_id:string;pert_type:string})=>`${row.cell_id} · ${row.pert_type}`},{title:'剂量',dataIndex:'dose',width:110},{title:'时间',dataIndex:'time',width:100},{title:'签名数',dataIndex:'n_signatures',width:90},{title:'WTCS 中位数',dataIndex:'WTCS_median',width:130,render:(value:string)=>Number(value).toFixed(4)},{title:'反向分数 −WTCS',render:(_:unknown,row:{WTCS_median:string})=>(-Number(row.WTCS_median)).toFixed(4)},{title:'条件内排名',dataIndex:'rank_within_condition',width:100},{title:'质量 Q75 中位数',dataIndex:'quality_cc_median',width:130,render:(value:string)=>Number(value).toFixed(3)}]
    const stabilityColumns=[{title:'药物',dataIndex:'drug_name'},{title:'LINCS ID',dataIndex:'pert_id',render:(value:string)=><Text code>{value}</Text>},{title:'细胞/扰动/时间',render:(_:unknown,row:{cell_id:string;pert_type:string;time:string})=>`${row.cell_id} · ${row.pert_type} · ${row.time}`},{title:'剂量条件数',dataIndex:'dose_count'},{title:'进入 Top 10 的条件数',dataIndex:'top_n_condition_count'},{title:'Top 10 复现率',dataIndex:'top_n_condition_fraction',render:(value:number)=>`${(value*100).toFixed(1)}%`},{title:'条件排名范围',render:(_:unknown,row:{best_condition_rank:number;worst_condition_rank:number})=>`${row.best_condition_rank}–${row.worst_condition_rank}`}]
    return <>{projectRunForm}<div className="page-heading"><div><Text className="eyebrow">筛选结果 / 项目级 LINCS S2</Text><Title level={2}>药物扰动条件结果</Title><Text type="secondary">运行 {projectS2.data.analysis_run_id} · {projectS2.data.cell_id} · {projectS2.data.time}</Text></div></div><Alert type={projectS2.data.test_only?'warning':'info'} showIcon message={projectS2.data.test_only?'软件测试结果（test_only），不是科研候选排名':`共 ${projectS2.data.signature_count} 条签名、${projectS2.data.drug_count} 个扰动药物、${projectS2.data.condition_count} 个剂量/时间条件`} description={`WTCS 保留原始方向；条件内按中位 WTCS 排名。${projectS2.data.dose_policy??'剂量分层保留'} 不把不同剂量或时间合并。结果来源：${conditions.data?.storage==='database'?'PostgreSQL 版本化条件表':conditions.data?.storage==='verified_csv'?'哈希核验的旧版运行 CSV':'读取中'}。`} style={{marginBottom:12}}/><Card title="跨剂量排名复现情况" className="section-card"><Alert type="info" showIcon message="这是稳定性指标，不是药效总排名" description={stability.data?.aggregation_policy??'按细胞、扰动类型和时间分层统计各剂量条件中进入 Top 10 的复现率；不合并 WTCS。'}/><Table rowKey={(row)=>`${row.pert_id}|${row.cell_id}|${row.pert_type}|${row.time}`} size="small" dataSource={stability.data?.items??[]} columns={stabilityColumns} loading={stability.isLoading} pagination={{pageSize:10}} /></Card><Card title="剂量/时间条件原始汇总" className="section-card"><Table rowKey={(row)=>`${row.pert_id}|${row.cell_id}|${row.pert_type}|${row.dose}|${row.time}`} size="small" dataSource={conditions.data?.items??[]} columns={conditionColumns} loading={conditions.isLoading} pagination={{current:Math.floor(offset/10)+1,pageSize:10,total:conditions.data?.total??0,onChange:(page)=>setOffset((page-1)*10)}} scroll={{x:1350}} /></Card></>
  }
    return <>{projectRunForm}<div className="page-heading"><div><Text className="eyebrow">筛选结果 / S2</Text><Title level={2}>候选药物综合证据</Title><Text type="secondary">WTCS 负值表示表达反向关联；PRISM 是独立的细胞活力观察。各证据列分别呈现，不合成未经验证的疗效总分。</Text></div></div>{q.data?.available?<><Alert type="info" showIcon message={`显示 ${q.data.total} 个候选；GraphBuild ${q.data.graph_build_id}；整合矩阵 SHA-256 ${q.data.source_sha256?.slice(0,12)??'已登记'}`} description="数据按 LINCS 扰动药物 ID 联结 Exp006–Exp011、项目 S2 全剂量条件及 GraphBuild 机制路径。图谱未纳入 Exp006 Top50 的候选明确标记未评估；剂量条件仍以逐条件 JSON 保留。排名沿用 Exp006，不重新计算最终药物排名。"/><Card className="section-card"><Table rowKey="pert_id" dataSource={q.data.items} columns={columns} pagination={{current:Math.floor(offset/10)+1,pageSize:10,total:q.data.total,onChange:(page)=>setOffset((page-1)*10)}} scroll={{x:2400}} /></Card></>:<Alert type="info" showIcon message="该项目暂无综合 S2 证据矩阵" description="新项目不复用 ER 阳性乳腺癌候选结果；请先完成并审核该项目自己的 S1/S2 分析。"/>}</>
}

function ProjectS2RunForm({projectId,projectStatus}:{projectId:string;projectStatus:string}) {
  const testOnly=projectStatus==='test_only'
  const runs=useQuery({queryKey:['project-runs',projectId],queryFn:()=>api.runs(projectId)})
  const eligibleS1=(runs.data??[]).filter(run=>run.status==='completed'&&['s1_precomputed_deg','s1_limma_microarray','s1_rnaseq_edger_voom'].includes(run.run_type))
  const [s1RunId,setS1RunId]=useState<string>()
  const [identifierType,setIdentifierType]=useState<'symbol'|'entrez'|'ensembl'>('symbol')
  const [fdr,setFdr]=useState(0.05); const [topN,setTopN]=useState(100)
  const [cellId,setCellId]=useState('MCF7'); const [perturbationType,setPerturbationType]=useState('trt_cp'); const [time,setTime]=useState('24 h'); const [quality,setQuality]=useState(0.2); const [maxSignatures,setMaxSignatures]=useState<number|undefined>(testOnly?5:undefined)
  const client=useQueryClient()
  useEffect(()=>{if(!s1RunId&&eligibleS1[0])setS1RunId(eligibleS1[0].analysis_run_id)},[eligibleS1,s1RunId])
  const run=useMutation({mutationFn:()=>{if(!s1RunId)throw new Error('请先完成并选择本项目的 S1 分析');return api.runProjectS2(projectId,{s1_analysis_run_id:s1RunId,identifier_type:identifierType,fdr_threshold:fdr,top_n:topN,cell_id:cellId.trim(),perturbation_type:perturbationType.trim(),time:time.trim(),min_distil_cc_q75:quality,...(testOnly?{max_signatures:maxSignatures}: {})})},onSuccess:async result=>{message.success(`S2 已完成：${result.analysis_run_id}；保存 ${result.condition_count} 条剂量/时间条件`);await Promise.all([client.invalidateQueries({queryKey:['project-s2-summary',projectId]}),client.invalidateQueries({queryKey:['project-s2-conditions',projectId]}),client.invalidateQueries({queryKey:['project-runs',projectId]})])},onError:(error:Error)=>message.error(`S2 运行失败：${error.message}`)})
  const start=()=>{if(testOnly){run.mutate();return}Modal.confirm({title:'启动完整 LINCS 筛选？',content:'将按当前条件读取并评分全部合格的 MCF7 药物 Signature。完整运行可能持续较长时间；运行日志、输入哈希和每个剂量/时间条件的结果会保留。',okText:'启动完整筛选',cancelText:'取消',onOk:()=>run.mutateAsync()})}
  return <Card title="配置并运行项目级 S2（LINCS）" className="section-card"><Alert type={testOnly?'warning':'info'} showIcon message={testOnly?'软件测试项目：仅允许少量签名测试':'完整筛选：用户确认后运行全部符合条件的 Signature'} description={testOnly?'默认最多读取 5 条签名，输出会保留 test_only 标记，不能导入正式科研项目。':'先完成项目级 S1；默认筛选 MCF7、trt_cp、24 h、CC Q75 ≥ 0.2，并按剂量分层保存。'} style={{marginBottom:12}}/><Space wrap><Select style={{minWidth:360}} value={s1RunId} placeholder="选择本项目已完成的 S1 运行" loading={runs.isLoading} options={eligibleS1.map(item=>({value:item.analysis_run_id,label:`${runTypeLabel(item.run_type)} · ${item.analysis_run_id}`}))} onChange={setS1RunId}/><Select value={identifierType} onChange={setIdentifierType} options={[{value:'symbol',label:identifierLabel('symbol')},{value:'entrez',label:identifierLabel('entrez')},{value:'ensembl',label:identifierLabel('ensembl')}]}/><InputNumber min={1e-6} max={1} step={0.01} value={fdr} onChange={value=>setFdr(Number(value??0.05))} addonBefore="FDR"/><InputNumber min={1} max={500} value={topN} onChange={value=>setTopN(Number(value??100))} addonBefore="每方向 Top N"/><Input value={cellId} onChange={event=>setCellId(event.target.value)} addonBefore="细胞" style={{width:190}}/><Input value={perturbationType} onChange={event=>setPerturbationType(event.target.value)} addonBefore="扰动类型" style={{width:210}}/><Input value={time} onChange={event=>setTime(event.target.value)} addonBefore="时间" style={{width:170}}/><InputNumber min={0} max={1} step={0.05} value={quality} onChange={value=>setQuality(Number(value??0.2))} addonBefore="CC Q75 ≥"/>{testOnly&&<InputNumber min={1} max={100} value={maxSignatures} onChange={value=>setMaxSignatures(value==null?undefined:Number(value))} addonBefore="最多签名"/>}<Button type="primary" loading={run.isPending} disabled={!s1RunId||!cellId.trim()||!perturbationType.trim()||!time.trim()||(testOnly&&!maxSignatures)} onClick={start}>{testOnly?'运行少量测试':'运行完整 S2'}</Button></Space>{!eligibleS1.length&&<Text type="secondary" style={{display:'block',marginTop:10}}>该项目还没有已完成的 S1 运行；先在 S1 页面上传并分析数据。</Text>}</Card>
}
