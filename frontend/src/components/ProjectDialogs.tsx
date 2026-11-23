import { useState } from 'react'
import { Alert, Button, Form, Input, Modal, Select, message } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, Project, Study } from '../api'

type ProjectDialogProps = {
  project?: Project
  createOpen: boolean
  uploadOpen: boolean
  onCloseCreate: () => void
  onCloseUpload: () => void
  onProjectCreated: (project: Project) => void
}

export default function ProjectDialogs({ project, createOpen, uploadOpen, onCloseCreate, onCloseUpload, onProjectCreated }: ProjectDialogProps) {
  const queryClient = useQueryClient()
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [datasetType, setDatasetType] = useState<'expression_matrix' | 'precomputed_deg' | 'sample_metadata'>('expression_matrix')
  const [studyId, setStudyId] = useState<string | undefined>()
  const [projectForm] = Form.useForm<{ name: string; disease_id: string; status: 'active' | 'test_only' }>()
  const [studyForm] = Form.useForm<{ accession: string; title: string }>()
  const studiesQuery = useQuery({ queryKey: ['studies', project?.project_id], queryFn: () => api.studies(project!.project_id), enabled: uploadOpen && Boolean(project) })

  const createStudy = useMutation({
    mutationFn: (values: { accession: string; title: string }) => {
      if (!project) throw new Error('请先选择项目')
      return api.createStudy(project.project_id, { ...values, organism: 'Homo sapiens' })
    },
    onSuccess: (study) => {
      queryClient.setQueryData<Study[]>(['studies', project?.project_id], (old) => [...(old ?? []).filter((row) => row.study_id !== study.study_id), study])
      setStudyId(study.study_id)
      studyForm.resetFields()
      message.success(`研究 ${study.accession} 已登记`)
    },
    onError: (error: Error) => message.error(`研究登记失败：${error.message}`),
  })

  const createProject = useMutation({
    mutationFn: api.createProject,
    onSuccess: (created) => {
      queryClient.setQueryData<Project[]>(['projects'], (old) => [...(old ?? []), created])
      onProjectCreated(created)
      onCloseCreate()
      projectForm.resetFields()
      message.success('项目已创建；尚未登记或运行分析数据。')
    },
    onError: (error: Error) => message.error(`创建失败：${error.message}`),
  })

  const uploadDataset = useMutation({
    mutationFn: () => {
      if (!project || !uploadFile) throw new Error('请先选择项目和文件')
      return api.uploadDataset(project.project_id, uploadFile, datasetType, studyId)
    },
    onSuccess: async (result) => {
      message.success(`文件已登记，状态 ${result.state}；没有自动启动分析。SHA-256 ${result.sha256.slice(0, 12)}…`)
      onCloseUpload()
      setUploadFile(null)
      setStudyId(undefined)
      studyForm.resetFields()
      await queryClient.invalidateQueries({ queryKey: ['datasets', project?.project_id] })
    },
    onError: (error: Error) => message.error(`上传失败：${error.message}`),
  })

  const submitProject = (values: { name: string; disease_id: string; status: 'active' | 'test_only' }) => createProject.mutate({
    slug: `project-${crypto.randomUUID().slice(0, 8)}`,
    name: values.name.trim(),
    disease_id: values.disease_id.trim(),
    status: values.status,
  })

  return <>
    <Modal title="新建疾病项目" open={createOpen} onCancel={onCloseCreate} onOk={() => projectForm.submit()} confirmLoading={createProject.isPending} okText="创建项目" cancelText="取消">
      <Alert type="info" showIcon message="新项目不会继承其他项目的分析结果" description="软件测试项目会与正式研究项目隔离，不能将测试结果作为科研结论。" style={{ marginBottom: 16 }} />
      <Form form={projectForm} layout="vertical" initialValues={{ status: 'active' }} onFinish={submitProject}>
        <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }, { min: 2, message: '至少输入 2 个字符' }]}>
          <Input placeholder="例如：肺腺癌表达逆转研究" />
        </Form.Item>
        <Form.Item name="disease_id" label="疾病标准 ID" extra="请核对项目对应的 MONDO 或 EFO ID；系统不会自动套用乳腺癌疾病 ID。" rules={[{ required: true, message: '请输入疾病 ID' }, { pattern: /^(MONDO|EFO):\d+$/, message: '请输入 MONDO 或 EFO 标准 ID' }]}>
          <Input placeholder="MONDO:<编号> 或 EFO:<编号>" />
        </Form.Item>
        <Form.Item name="status" label="项目用途">
          <Select options={[{ value: 'active', label: '正式研究项目' }, { value: 'test_only', label: '软件测试项目（test_only）' }]} />
        </Form.Item>
      </Form>
    </Modal>
    <Modal title="上传项目数据" open={uploadOpen} onCancel={() => { onCloseUpload(); setUploadFile(null); setStudyId(undefined); studyForm.resetFields() }} onOk={() => uploadDataset.mutate()} confirmLoading={uploadDataset.isPending} okButtonProps={{ disabled: !uploadFile || !project }} okText="上传并校验" cancelText="取消">
      <Alert type="info" showIcon message="上传后仅做格式和完整性校验" description="支持不超过 250 MB 的 CSV/TSV/TXT。数据进入 validation_pending，不会自动启动差异分析；表达矩阵需另行登记样本分组信息。" style={{ marginBottom: 16 }} />
      <Form form={studyForm} layout="inline" onFinish={(values) => createStudy.mutate({ accession: values.accession.trim(), title: values.title.trim() })} style={{ marginBottom: 12 }}>
        <Form.Item name="accession" rules={[{ required: true, message: '请输入 GEO 或其他研究编号' }]}>
          <Input placeholder="研究编号，如 GSE42568" />
        </Form.Item>
        <Form.Item name="title" rules={[{ required: true, message: '请输入研究名称' }]}>
          <Input placeholder="研究名称" />
        </Form.Item>
        <Button htmlType="submit" loading={createStudy.isPending}>登记研究</Button>
      </Form>
      <Select allowClear value={studyId} onChange={setStudyId} loading={studiesQuery.isLoading} placeholder="将数据关联到研究（可选）" style={{ width: '100%', marginBottom: 16 }} options={(studiesQuery.data ?? []).map((study) => ({ value: study.study_id, label: `${study.accession} · ${study.title}` }))} />
      <div style={{ marginBottom: 16 }}>
        <label htmlFor="dataset-type">数据类型</label>
        <Select id="dataset-type" value={datasetType} onChange={setDatasetType} style={{ width: '100%', marginTop: 8 }} options={[{ value: 'expression_matrix', label: '表达矩阵（基因 × 样本）' }, { value: 'precomputed_deg', label: '已计算差异表达结果' }, { value: 'sample_metadata', label: '样本分组注释' }]} />
      </div>
      <label htmlFor="dataset-file">选择数据文件（CSV、TSV 或 TXT）</label>
      <input id="dataset-file" name="dataset-file" type="file" accept=".csv,.tsv,.txt" aria-label="选择项目数据文件" onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)} />
      {uploadFile && <p className="upload-selection">已选择：{uploadFile.name}（{(uploadFile.size / 1024 / 1024).toFixed(2)} MB）</p>}
    </Modal>
  </>
}
