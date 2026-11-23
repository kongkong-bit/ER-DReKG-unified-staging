import { NavLink } from 'react-router-dom'
import { Alert, Button, Card, Empty, Modal, Spin, Statistic, Table, Tag, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../api'
import { Loading, useProject } from '../projectContext'
import { contrastLabel, projectLabel, runTypeLabel, statusLabel, studyTitleLabel } from '../locales/zh-CN'

const { Title, Text } = Typography

export default function Dashboard() {
  const { isLoading, error, project } = useProject()
  const [statusRunId,setStatusRunId]=useState<string>()
  const [selectedMetric,setSelectedMetric]=useState<string>()
  const s1 = useQuery({ queryKey: ['s1', project?.project_id], queryFn: () => api.s1(project!.project_id), enabled: !!project })
  const candidates = useQuery({ queryKey: ['candidates', project?.project_id], queryFn: () => api.candidates(project!.project_id), enabled: !!project })
  const s2 = useQuery({ queryKey:['project-s2-summary',project?.project_id], queryFn:()=>api.s2Summary(project!.project_id), enabled:!!project })
  const graph = useQuery({ queryKey: ['graph-summary', project?.project_id], queryFn: () => api.graphSummary(project!.project_id), enabled: !!project })
  const datasets = useQuery({queryKey:['datasets',project?.project_id],queryFn:()=>api.datasets(project!.project_id),enabled:!!project})
  const runs = useQuery({queryKey:['project-runs',project?.project_id],queryFn:()=>api.runs(project!.project_id),enabled:!!project})
  const status = useQuery({queryKey:['job-status',statusRunId],queryFn:()=>api.jobStatus(statusRunId!),enabled:!!statusRunId})
  if (isLoading) return <Loading />
  if (error) return <Loading error={error as Error} />
  if (!project) return <Empty description="暂无项目" />
  return <>
    <div className="page-heading"><div><Text className="eyebrow">研究项目 / {project.disease_id||'软件测试项目'}</Text><Title level={2}>{projectLabel(project.name, project.slug)}</Title><Text type="secondary">{String(s1.data?.dataset??'尚无 S1 数据')} · {contrastLabel(typeof s1.data?.contrast === 'string' ? s1.data.contrast : undefined)} · 项目状态：{statusLabel(project.status)}</Text></div><Tag color={project.status==='test_only'?'gold':'blue'}>{project.status==='test_only'?'仅软件测试':'正式研究项目'}</Tag></div>
    <div className="stats-grid">
      <MetricCard id="s1-tested" selected={selectedMetric==='s1-tested'} onSelect={setSelectedMetric} title="S1 检验基因" value={s1.data?.tested_genes as number ?? '—'} suffix="个" />
      <MetricCard id="s1-significant" selected={selectedMetric==='s1-significant'} onSelect={setSelectedMetric} title="显著差异基因" value={s1.data?.significant_genes_fdr05 as number ?? '—'} suffix="个" />
      <MetricCard id="graph-nodes" selected={selectedMetric==='graph-nodes'} onSelect={setSelectedMetric} title="知识图谱局部子图" value={graph.data?.node_count ?? '—'} suffix="节点" />
    </div>
    <Card title="数据集与导入状态" className="section-card">
      {datasets.error ? <Alert type="error" message={(datasets.error as Error).message} /> : <Table
        rowKey="dataset_id"
        size="small"
        dataSource={datasets.data?.items ?? []}
        pagination={{ pageSize: 5 }}
        locale={{ emptyText: '该项目还没有登记数据' }}
        columns={[
          { title: '文件 / 来源', dataIndex: 'filename', render: (name: string | undefined, row: { source: string }) => name ?? row.source },
          { title: '研究', dataIndex: 'study', render: (study: { accession: string; title: string } | null | undefined) => study ? `${study.accession} · ${studyTitleLabel(study.accession, study.title)}` : '未关联' },
          { title: '数据类型', dataIndex: 'validation', render: (value: Record<string, unknown>) => ({ expression_matrix: '表达矩阵', precomputed_deg: '预计算差异表达表', sample_metadata: '样本分组注释' }[String(value.dataset_type)] ?? String(value.dataset_type ?? '已登记数据')) },
          { title: '校验状态', dataIndex: 'state', render: (value: string) => <Tag color={value === 'validation_pending' ? 'gold' : 'green'}>{value === 'validation_pending' ? '待校验' : statusLabel(value)}</Tag> },
          { title: '行数', dataIndex: 'validation', render: (value: Record<string, unknown>) => String(value.row_count ?? '—') },
          { title: '样本数', dataIndex: 'validation', render: (value: Record<string, unknown>) => String(value.sample_count ?? '—') },
        ]}
      />}
    </Card>
    <Card title="实验流程" className="section-card"><div className="timeline"><span className={s1.data?.available ? 'done' : 'current'}>S1 差异分析</span><i/><span className={(candidates.data?.total ?? 0) > 0 ? 'done' : 'current'}>S2 表达逆转筛选</span><i/><span className={project.slug === 'erpos-gse42568' ? 'done' : 'current'}>外部队列与 PRISM 验证</span><i/><span className={(graph.data?.node_count ?? 0) > 0 ? 'done' : 'current'}>知识图谱</span></div><Alert type="warning" showIcon message="证据边界" description="WTCS 表达逆转、PRISM 细胞存活和公共知识图谱关系是不同证据；当前结果不等同于临床疗效证明。新建项目仅显示已经登记的数据，不复用 ER+ 项目的分析结果。" /></Card>
    <Card title="最近分析运行" className="section-card" extra={<NavLink to="/compare">查看可靠性分析</NavLink>}><Table rowKey="analysis_run_id" size="small" dataSource={(runs.data??[]).slice(0,10)} pagination={false} locale={{emptyText:'该项目暂无分析运行'}} columns={[{title:'分析类型',dataIndex:'run_type',render:(value:string)=>runTypeLabel(value)},{title:'运行 ID',dataIndex:'analysis_run_id',render:(id:string)=><Text code>{id}</Text>},{title:'状态',dataIndex:'status',render:(value:string)=><Tag color={value==='completed'||value==='materialized'?'green':value==='failed'?'red':'gold'}>{statusLabel(value)}</Tag>},{title:'创建时间',dataIndex:'created_at'},{title:'详情',render:(_:unknown,row:{analysis_run_id:string})=><Button type="link" onClick={()=>setStatusRunId(row.analysis_run_id)}>查看状态</Button>}]} /></Card>
    <Modal title="分析运行状态" open={!!statusRunId} onCancel={()=>setStatusRunId(undefined)} footer={null}>{status.isLoading?<Spin/>:status.error?<Alert type="error" message={(status.error as Error).message}/>:status.data?<><Text code>{status.data.analysis_run_id}</Text><p><Tag color={status.data.state==='completed'?'green':status.data.state==='failed'?'red':'gold'}>{statusLabel(status.data.state)}</Tag>{status.data.progress==null?'同步工作，不报告异步百分比':`进度 ${status.data.progress}%`}</p><Text type="secondary">{status.data.description}</Text></>:null}</Modal>
  </>
}

function MetricCard({ id, title, value, suffix, selected, onSelect }: { id: string; title: string; value: string | number; suffix: string; selected: boolean; onSelect: (id: string) => void }) {
  const select = () => onSelect(id)
  return <Card
    className={`dashboard-metric-card${selected ? ' is-selected' : ''}`}
    role="button"
    tabIndex={0}
    aria-pressed={selected}
    onClick={select}
    onKeyDown={(event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        select()
      }
    }}
  >
    <Statistic title={title} value={value} suffix={suffix} />
  </Card>
}
