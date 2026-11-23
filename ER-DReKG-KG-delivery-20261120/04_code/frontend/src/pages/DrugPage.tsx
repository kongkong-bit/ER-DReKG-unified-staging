import { useEffect, useState } from 'react'
import { Alert, Button, Card, Empty, Modal, Select, Space, Spin, Statistic, Table, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api, isGraphBuildQueryable } from '../api'
import { Loading, useProject } from '../projectContext'

const { Title, Text } = Typography

export default function DrugPage() {
  const { project } = useProject()
  const navigate = useNavigate()
  const candidates = useQuery({queryKey:['candidates',project?.project_id],queryFn:()=>api.candidates(project!.project_id),enabled:!!project})
  const integrated = useQuery({queryKey:['drug-integrated-evidence',project?.project_id],queryFn:()=>api.evidenceMatrix(project!.project_id,0,100),enabled:!!project})
  const conditions = useQuery({queryKey:['drug-all-s2-conditions',project?.project_id],queryFn:()=>api.s2AllConditions(project!.project_id),enabled:!!project})
  const stability = useQuery({queryKey:['drug-s2-stability',project?.project_id],queryFn:()=>api.s2Stability(project!.project_id),enabled:!!project})
  const builds = useQuery({queryKey:['graph-builds',project?.project_id],queryFn:()=>api.graphBuilds(project!.project_id),enabled:!!project})
  const activeBuildId = (builds.data?.items ?? []).find(isGraphBuildQueryable)?.graph_build_id
  const [pertId,setPertId]=useState<string>()
  const [evidenceId,setEvidenceId]=useState<string>()
  useEffect(()=>setPertId(candidates.data?.items[0]?.pert_id),[project?.project_id,candidates.data])
  const q=useQuery({queryKey:['mechanisms',project?.project_id,pertId,activeBuildId],queryFn:()=>api.mechanisms(project!.project_id,pertId!,activeBuildId),enabled:!!project&&!!pertId})
  const evidence=useQuery({queryKey:['evidence',evidenceId,activeBuildId],queryFn:()=>api.evidence(evidenceId!,activeBuildId),enabled:!!evidenceId})
  const kg07 = useMutation({mutationFn:(mode:'kg_llm'|'kg_rule'|'direct_llm')=>api.kg07Interpret(project!.project_id,pertId!,activeBuildId,mode)})
  const options=(candidates.data?.items??[]).map(item=>({value:item.pert_id,label:`${item.drug_name} · ${item.pert_id}`}))
  const candidate=(candidates.data?.items??[]).find(item=>item.pert_id===pertId)
  const evidenceRow=integrated.data?.items.find(item=>item.pert_id===pertId)
  const goPath=(pathId:string)=>navigate(`/graph?pert_id=${encodeURIComponent(pertId??'')}&path_id=${encodeURIComponent(pathId)}&graph_build_id=${encodeURIComponent(activeBuildId??'')}`)
  const exportInterpretation=()=>{if(!kg07.data)return;const blob=new Blob([JSON.stringify(kg07.data,null,2)],{type:'application/json'});const anchor=document.createElement('a');anchor.href=URL.createObjectURL(blob);anchor.download=`kg07_${pertId}_${kg07.data.prompt_version}.json`;anchor.click();URL.revokeObjectURL(anchor.href)}
  const explanation=kg07.data?.explanation
  const interpretationSections=[['筛选依据','screening_basis'],['已知靶点','known_targets'],['相关通路','associated_pathways'],['独立验证','independent_validation'],['机制假设','mechanism_hypotheses'],['证据不足','insufficient_evidence']] as const
  const doseRows=(conditions.data??[]).filter(item=>item.pert_id===pertId)
  const stabilityRow=stability.data?.items.find(item=>item.pert_id===pertId)
  const routes=(q.data?.routes??[]) as Array<Record<string,unknown>>
  return <><div className="page-heading"><div><Text className="eyebrow">候选详情 / 证据与机制</Text><Title level={2}>药物详情</Title><Text type="secondary">不同数据源分项展示；体外敏感性和表达逆转都不等同于临床疗效。</Text></div><Select showSearch optionFilterProp="label" loading={candidates.isLoading} value={pertId} onChange={setPertId} options={options} placeholder="选择项目候选药物" style={{width:360}} /></div>{candidates.error?<Loading error={candidates.error as Error}/>:!options.length&&!candidates.isLoading?<Empty description="该项目没有已登记的候选药物"/>:q.isLoading?<Loading/>:q.error?<Loading error={q.error as Error}/>:<>
    {(integrated.error||conditions.error||stability.error)&&<Alert type="warning" showIcon message="部分外部证据暂不可用" description={[integrated.error,conditions.error,stability.error].filter(Boolean).map(error=>(error as Error).message).join('；')}/>}
    <Alert type="info" showIcon message={q.data?.interpretation}/>
    {candidate&&<Card title={`${candidate.drug_name} · ${candidate.pert_id}`} className="section-card"><div className="stats-grid"><Card><Statistic title="Exp006 原排名" value={evidenceRow?.rank??candidate.rank} suffix="位"/></Card><Card><Statistic title="历史 B 方案 WTCS 中位数" value={Number(evidenceRow?.wtcs_median_B??candidate.score_value)} precision={4}/></Card><Card><Statistic title="剂量条件数" value={doseRows.length||'—'} suffix="个"/></Card><Card><Statistic title="跨剂量 Top 10 复现率" value={stabilityRow?`${(stabilityRow.top_n_condition_fraction*100).toFixed(0)}%`:'—'}/></Card><Card><Statistic title="独立 S1 中位排名" value={evidenceRow?.external_s1_median_rank||'—'} suffix={evidenceRow?.external_s1_median_rank?'位':''}/></Card><Card><Statistic title="PRISM ER+ 平均敏感性" value={evidenceRow?.erpos_mean_sensitivity||'—'}/></Card><Card><Statistic title="PRISM ER− 平均敏感性" value={evidenceRow?.erneg_mean_sensitivity||'—'}/></Card><Card><Statistic title="Exp006 稳定性标记" value={evidenceRow?.stability_grade||'—'}/></Card></div><Text type="secondary">PRISM 数值表示细胞活力实验中的相对敏感性；S2 WTCS 是表达关联分数。数据缺失时显示“—”，不按名称补配。证据来源：Exp006–Exp011 综合矩阵、项目级 S2 条件与版本化 GraphBuild。</Text></Card>}
    <Card title={`LINCS 剂量/时间条件（${doseRows.length} 条；不跨条件合并 WTCS）`} className="section-card"><Table rowKey={(row)=>`${row.pert_id}|${row.cell_id}|${row.pert_type}|${row.dose}|${row.time}`} size="small" dataSource={doseRows} loading={conditions.isLoading} pagination={{pageSize:10}} scroll={{x:1200}} columns={[{title:'细胞 / 扰动',render:(_:unknown,row)=>`${row.cell_id} · ${row.pert_type}`},{title:'剂量',dataIndex:'dose'},{title:'时间',dataIndex:'time'},{title:'Signature 数',dataIndex:'n_signatures'},{title:'WTCS 中位数',dataIndex:'WTCS_median',render:(value:string)=>Number(value).toFixed(4)},{title:'质量 CC Q75 中位数',dataIndex:'quality_cc_median',render:(value:string)=>value?Number(value).toFixed(3):'—'},{title:'剂量内排名',dataIndex:'rank_within_condition'}]}/></Card>
    <Card title={`机制与来源证据路径（${routes.length} 条；最多显示 100 条）`} className="section-card"><Table rowKey={(_,i)=>String(i)} dataSource={routes.slice(0,100)} pagination={{pageSize:10}} columns={[{title:'路径类型',dataIndex:'route_type',render:(value:string)=>value==='s1_enrichment_overlap'?'S1 富集证据交汇':'公共知识图谱'},{title:'药物实体',dataIndex:'drug_id'},{title:'靶基因',dataIndex:'target_gene_id'},{title:'通路',dataIndex:'pathway_label',render:(value:string,record:Record<string,unknown>)=>value||String(record.pathway_id||'—')},{title:'来源记录',dataIndex:'evidence_ids',render:(ids:string[])=>ids?.length?<Space wrap>{ids.map((id,index)=><Button key={id} type="link" onClick={()=>setEvidenceId(id)}>证据 {index+1}</Button>)}</Space>:'—'}]} /></Card>
    <Card title="AI 机制解释（证据引用已由后端校验）" className="section-card">
      <Space wrap><Button type="primary" loading={kg07.isPending} disabled={!activeBuildId} onClick={()=>kg07.mutate('kg_llm')}>生成 KG + AI 解释</Button><Button loading={kg07.isPending} disabled={!activeBuildId} onClick={()=>kg07.mutate('kg_rule')}>规则模板对照</Button>{kg07.data&&<Button onClick={exportInterpretation}>导出 JSON</Button>}</Space>
      {kg07.isPending&&<Alert style={{marginTop:12}} type="info" showIcon message="正在基于当前项目、GraphBuild 和证据包生成解释…"/>}
      {kg07.error&&<Alert style={{marginTop:12}} type="error" showIcon message="解释生成失败" description={(kg07.error as Error).message}/>}
      {kg07.data&&<div style={{marginTop:16}}>
        <Alert type={kg07.data.citation_reference_validation_pass?'success':'warning'} showIcon message={kg07.data.citation_reference_validation_pass?'引用 ID 与当前证据包匹配；语义支持仍需人工审核':'存在未通过引用核验或证据不足的内容'} description={`模型：${kg07.data.model??'规则模板'} · Prompt：${kg07.data.prompt_version} · 输入哈希：${kg07.data.evidence_input_sha256} · ${kg07.data.cached?'命中缓存':`耗时 ${kg07.data.latency_seconds}s`} · 费用：${kg07.data.provider_cost_status==='reported'?kg07.data.provider_cost:'服务方未返回费用信息'} · ${kg07.data.semantic_entailment_status??'需人工复核生物学解释'}`}/>
        {!!kg07.data.evidence_gaps?.length&&<Alert style={{marginTop:10}} type="warning" showIcon message="检索到的证据缺口" description={kg07.data.evidence_gaps.join('；')}/>}
        {interpretationSections.map(([label,key])=>{const value=explanation?.[key];if(value==null||value===''||(Array.isArray(value)&&!value.length))return null;return <Card key={key} size="small" title={label} style={{marginTop:10}}>{Array.isArray(value)?<Space direction="vertical" style={{width:'100%'}}>{value.map((claim:Record<string,any>,index:number)=><div key={`${key}-${index}`}><Text>{claim.text}</Text><Space wrap style={{marginLeft:8}}>{(claim.path_ids??[]).map((id:string)=><Button size="small" key={id} onClick={()=>goPath(id)}>路径 {id.slice(0,10)}…</Button>)}{(claim.evidence_ids??[]).map((id:string)=><Button size="small" key={id} onClick={()=>setEvidenceId(id)}>证据 {id.slice(0,10)}…</Button>)}</Space>{claim.relation&&<Text type="secondary"> · 关系类型：{claim.relation}</Text>}<Text type="secondary"> · 语义支持需人工审核</Text></div>)}</Space>:<Text>{String(value)}</Text>}</Card>})}
        {!!explanation?.limitations?.length&&<Alert style={{marginTop:10}} type="warning" showIcon message="局限性" description={(explanation.limitations as string[]).join('；')}/>}
        {!!kg07.data.citation_validation_issues?.length&&<Alert style={{marginTop:10}} type="warning" showIcon message="引用校验记录" description={`${kg07.data.citation_validation_issues.length} 项声明被降级、删除或标记待人工检查。`}/>}
      </div>}
    </Card>
    {evidenceRow?.evidence_limitations&&<Alert type="warning" showIcon message="证据限制" description={evidenceRow.evidence_limitations}/>}
  </>}<Modal title="原始证据记录" open={!!evidenceId} onCancel={()=>setEvidenceId(undefined)} footer={null} width={760}>{evidence.isLoading?<Spin/>:evidence.error?<Alert type="error" message={(evidence.error as Error).message}/>:<pre style={{maxHeight:500,overflow:'auto',whiteSpace:'pre-wrap'}}>{JSON.stringify(evidence.data,null,2)}</pre>}</Modal></>
}
