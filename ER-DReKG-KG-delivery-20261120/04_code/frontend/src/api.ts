export type Project = { project_id: string; slug: string; name: string; disease_id: string; status: string; created_at: string }
export type Study = { study_id:string;project_id:string;accession:string;title:string;organism:string;design_json:Record<string,unknown>;created_at:string }
export type Candidate = { candidate_id: string; pert_id: string; drug_name: string; rank: number; score_name: string; score_value: string; evidence: Record<string, unknown> }
export type GraphNode = { id: string; type: string; label: string; properties: Record<string, unknown> }
export type GraphEdge = { id: string; source: string; target: string; relation: string; evidence_ids: string[] }
export type Subgraph = { project_id: string; analysis_run_id?: string; nodes: GraphNode[]; edges: GraphEdge[]; truncated: boolean; next_cursor?: string | null }
export type GraphSearchResult = { id: string; type: string; label: string }
export type PathwayCollection = 'go_up' | 'go_down' | 'reactome_up' | 'reactome_down' | 'hallmark_gsea'
export type PathwayItem = Record<string, string | number | null>
export type S1Gene = { gene_symbol: string; logFC: number; t: number; 'P.Value': number | null; 'adj.P.Val': number; direction: 'up' | 'down' | 'unchanged' }
export type VolcanoPoint = { gene_symbol: string; logFC: number; 'adj.P.Val': number; minus_log10_fdr: number; direction: 'up' | 'down' | 'not_significant' }
export type IntegratedEvidenceRow = Record<string, string>
export type S2Condition = { pert_id:string; drug_name:string; cell_id:string; pert_type:string; dose:string; time:string; n_signatures:string; WTCS_median:string; WTCS_mean:string; WTCS_sd:string; WTCS_mad:string; quality_cc_median:string; TAS_median:string; replicates_median:string; rank_within_condition:string }
export type S2Stability = {pert_id:string;drug_name:string;cell_id:string;pert_type:string;time:string;dose_count:number;condition_count:number;top_n:number;top_n_condition_count:number;top_n_condition_fraction:number;best_condition_rank:number;worst_condition_rank:number;rank_range_across_conditions:number;interpretation:string}
export type GraphBuild = { graph_build_id: string; analysis_run_id: string; status: string; graph_source: string; created_at: string; input_hashes: Record<string,string>; summary: Record<string,unknown> }
export const isGraphBuildQueryable = (build: GraphBuild): boolean =>
  build.graph_source === 'neo4j'
    ? build.status === 'materialized'
    : build.status === 'materialized' || build.status === 'materialized_snapshot'
export type AnalysisRun = { analysis_run_id:string; run_type:string; status:string; created_at:string; parameters:Record<string,unknown> }
export type RunComparison = { project_id:string;run_type:string;run_a:{analysis_run_id:string;run_type:string;status:string;created_at:string;parameters:Record<string,unknown>;software_versions:Record<string,unknown>;input_hashes:Record<string,string>;output_summary:Record<string,unknown>};run_b:{analysis_run_id:string;run_type:string;status:string;created_at:string;parameters:Record<string,unknown>;software_versions:Record<string,unknown>;input_hashes:Record<string,string>;output_summary:Record<string,unknown>};provenance_comparison:Record<string,unknown>;output_comparison:Record<string,any> }
export type ExternalS1Validation = {project_id:string;available:boolean;reason?:string|null;source_dataset?:string|null;validation_run?:string|null;sample_design:Record<string,number|string>;summary:Record<string,number>;offset:number;limit:number;total_conditions:number;items:Array<{pert_id:string;drug_name:string;cell_id:string;pert_type:string;dose:string;time:string;n_signatures:number;WTCS_median:number|null;CC_median:number|null;TAS_median:number|null;external_rank:number|null;B200_WTCS_median:number|null;B200_rank:number|null}>;provenance:Record<string,string>}

const request = async <T,>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`/api/v1${path}`, init)
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
  return response.json() as Promise<T>
}

export const api = {
  projects: () => request<Project[]>('/projects'),
  datasets: (id: string) => request<{items: Array<{dataset_id:string;study_id:string|null;study?:{accession:string;title:string}|null;source:string;release:string;sha256:string;state:string;license_status:string;filename?:string|null;validation:Record<string,unknown>}>}>(`/projects/${id}/datasets`),
  linkDatasetToStudy: (projectId:string,datasetId:string,studyId:string) => request(`/projects/${projectId}/datasets/${datasetId}/study`, {method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({study_id:studyId})}),
  studies: (id:string) => request<Study[]>(`/projects/${id}/studies`),
  runs: (id: string) => request<AnalysisRun[]>(`/projects/${id}/runs`),
  jobStatus: (jobId:string) => request<{job_id:string;analysis_run_id:string;project_id:string;state:string;progress:number|null;created_at:string;description:string}>(`/jobs/${encodeURIComponent(jobId)}`),
  compareRuns: (id:string,runAId:string,runBId:string) => {const query=new URLSearchParams({run_a_id:runAId,run_b_id:runBId});return request<RunComparison>(`/projects/${id}/runs/compare?${query}`)},
  createProject: async (payload: {slug: string; name: string; disease_id: string; status?: 'active'|'test_only'}) => {
    const response = await fetch('/api/v1/projects', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
    return response.json() as Promise<Project>
  },
  createStudy: async (projectId:string, payload:{accession:string;title:string;organism?:string;design_json?:Record<string,unknown>}) => {
    const response = await fetch(`/api/v1/projects/${projectId}/studies`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<Study>
  },
  uploadDataset: async (projectId: string, file: File, datasetType: 'expression_matrix' | 'precomputed_deg' | 'sample_metadata', studyId?:string) => {
    const params = new URLSearchParams({filename: file.name, dataset_type: datasetType})
    if (studyId) params.set('study_id', studyId)
    const response = await fetch(`/api/v1/projects/${projectId}/datasets/upload?${params}`, {method:'POST', headers:{'Content-Type':file.type||'application/octet-stream'}, body:file})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<{dataset_id:string; study_id:string|null; state:string; sha256:string; analysis_started:boolean}>
  },
  runPrecomputedS1: async (projectId: string, datasetId: string, payload: {positive_group:string;negative_group:string;fdr_threshold:number}) => {
    const response = await fetch(`/api/v1/projects/${projectId}/datasets/${datasetId}/s1/precomputed`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<{analysis_run_id:string;status:string;summary:Record<string,unknown>}>
  },
  runLimmaS1: async (projectId: string, datasetId: string, payload: {sample_metadata_dataset_id:string;positive_group:string;negative_group:string;identifier_type:'symbol'|'entrez'|'ensembl';fdr_threshold:number;measurement_type:'normalized_log2_microarray'}) => {
    const response = await fetch(`/api/v1/projects/${projectId}/datasets/${datasetId}/s1/limma-microarray`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<{analysis_run_id:string;status:string;summary:Record<string,unknown>}>
  },
  runRNASeqS1: async (projectId: string, datasetId: string, payload: {sample_metadata_dataset_id:string;positive_group:string;negative_group:string;identifier_type:'symbol'|'entrez'|'ensembl';fdr_threshold:number;measurement_type:'raw_integer_counts'}) => {
    const response = await fetch(`/api/v1/projects/${projectId}/datasets/${datasetId}/s1/rnaseq-edger-voom`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<{analysis_run_id:string;status:string;summary:Record<string,unknown>}>
  },
  runPathwayEnrichment: async (projectId:string,payload:{s1_analysis_run_id:string;identifier_type:'symbol'|'entrez'|'ensembl';fdr_threshold:number}) => {
    const response = await fetch(`/api/v1/projects/${projectId}/s1/pathway-enrichment`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<{analysis_run_id:string;status:string;summary:Record<string,unknown>;result_dir:string}>
  },
  s1: (id: string) => request<Record<string, unknown>>(`/projects/${id}/s1/summary`),
  s1ExternalValidation: (id:string,offset=0,limit=20) => request<ExternalS1Validation>(`/projects/${id}/s1/external-validation?${new URLSearchParams({offset:String(offset),limit:String(limit)})}`),
  s1Genes: (id: string, direction: 'all' | 'up' | 'down', page = 1, pageSize = 20) => request<{available: boolean; total: number; items: S1Gene[]}>(`/projects/${id}/s1/genes?direction=${direction}&significant_only=true&limit=${pageSize}&offset=${(page-1)*pageSize}`),
  s1Volcano: (id: string) => request<{available: boolean; total: number; fdr_threshold: number; points: VolcanoPoint[]}>(`/projects/${id}/s1/volcano`),
  pathways: (id: string, collection: PathwayCollection) => request<{ total: number; items: PathwayItem[] }>(`/projects/${id}/s1/pathways?collection=${collection}&limit=10`),
  candidates: (id: string) => request<{ items: Candidate[]; total: number; truncated: boolean }>(`/projects/${id}/s2/candidates?limit=50`),
  evidenceMatrix: (id: string, offset = 0, limit = 10) => request<{available: boolean; total: number; items: IntegratedEvidenceRow[]; sha256?: string; reason?: string}>(`/projects/${id}/s2/evidence-matrix?offset=${offset}&limit=${limit}`),
  candidateEvidence: (id: string, offset = 0, limit = 10) => request<{available:boolean;total:number;items:IntegratedEvidenceRow[];source_sha256?:string;graph_build_id?:string}>(`/projects/${id}/s2/candidate-evidence?offset=${offset}&limit=${limit}`),
  s2Summary: (id: string) => request<{available:boolean;analysis_run_id?:string|null;test_only?:boolean;condition_count?:number;signature_count?:number;drug_count?:number;time?:string;cell_id?:string;perturbation_type?:string;quality_threshold?:number;dose_policy?:string}>(`/projects/${id}/s2/summary`),
  s2Conditions: (id: string, offset = 0, limit = 50) => request<{available:boolean;analysis_run_id?:string;test_only?:boolean;items:S2Condition[];offset:number;limit:number;total:number;truncated?:boolean;storage?:'database'|'verified_csv'}>(`/projects/${id}/s2/conditions?offset=${offset}&limit=${limit}`),
  s2AllConditions: async (id: string) => {
    const rows: S2Condition[] = []
    let offset = 0
    let total = Number.POSITIVE_INFINITY
    while (offset < total) {
      const page = await request<{available:boolean;items:S2Condition[];total:number;offset:number;limit:number}>(`/projects/${id}/s2/conditions?offset=${offset}&limit=100`)
      total = page.total
      rows.push(...page.items)
      if (!page.items.length) break
      offset += page.items.length
    }
    return rows
  },
  s2Stability: (id:string,topN=10) => request<{available:boolean;analysis_run_id?:string;test_only?:boolean;top_n:number;storage?:'database'|'verified_csv';aggregation_policy?:string;items:S2Stability[]}>(`/projects/${id}/s2/stability?top_n=${topN}`),
  importS2Run: async (id: string, analysisRunId: string) => {
    const response = await fetch(`/api/v1/projects/${id}/s2/import`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({analysis_run_id:analysisRunId})})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<{analysis_run_id:string;status:string;idempotent:boolean;condition_count?:number}>
  },
  runProjectS2: async (id:string,payload:{s1_analysis_run_id:string;identifier_type:'symbol'|'entrez'|'ensembl';fdr_threshold:number;top_n:number;cell_id:string;perturbation_type:string;time:string;min_distil_cc_q75:number;max_signatures?:number}) => {
    const response = await fetch(`/api/v1/projects/${id}/s2/run`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<{analysis_run_id:string;status:string;test_only:boolean;condition_count:number;log_path:string;log_sha256:string;qc_summary:Record<string,unknown>}>
  },
  graphSummary: (id: string, buildId?: string) => request<{ graph_build_id?: string; node_count: number; edge_count: number; nodes_by_type: Record<string, number>; source: string }>(`/projects/${id}/graph/summary${buildId ? `?graph_build_id=${encodeURIComponent(buildId)}` : ''}`),
  graphBuilds: (id: string) => request<{items: GraphBuild[]}>(`/projects/${id}/graph-builds`),
  createProjectGraphBundle: async (id:string,payload:{s1_analysis_run_id:string;s2_analysis_run_id:string;enrichment_analysis_run_id:string}) => {
    const response = await fetch(`/api/v1/projects/${id}/graph-bundles`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<{analysis_run_id:string;status:string;test_only:boolean;bundle_dir:string;counts:Record<string,number>}>
  },
  buildProjectGraph: async (id:string,bundleRunId?:string) => {
    const query = bundleRunId ? `?bundle_run_id=${encodeURIComponent(bundleRunId)}` : ''
    const response = await fetch(`/api/v1/projects/${id}/graph-builds${query}`, {method:'POST'})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<GraphBuild & {detail:string;idempotent:boolean}>
  },
  registerGraphSnapshot: async (id: string) => {
    const response = await fetch(`/api/v1/projects/${id}/graph-builds`, {method:'POST'})
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`)
    return response.json() as Promise<GraphBuild & {detail:string;idempotent:boolean}>
  },
  graph: (id: string, cursor = 0, nodeId?: string, buildId?: string) => request<Subgraph>(`/projects/${id}/graph/subgraph?limit=100&max_depth=2&cursor=${cursor}${nodeId ? `&node_id=${encodeURIComponent(nodeId)}` : ''}${buildId ? `&graph_build_id=${encodeURIComponent(buildId)}` : ''}`),
  searchNodes: (id: string, query: string, buildId?: string) => request<{items: GraphSearchResult[]}>(`/projects/${id}/graph/search?q=${encodeURIComponent(query)}&limit=20${buildId ? `&graph_build_id=${encodeURIComponent(buildId)}` : ''}`),
  mechanisms: (id: string, pertId: string, buildId?: string) => request<{ routes: Array<Record<string, unknown>>; interpretation: string }>(`/projects/${id}/drugs/${encodeURIComponent(pertId)}/mechanisms${buildId ? `?graph_build_id=${encodeURIComponent(buildId)}` : ''}`),
  kg07Interpret: (id: string, pertId: string, buildId?: string, mode: 'kg_llm'|'kg_rule'|'direct_llm' = 'kg_llm') => request<Record<string, any>>(`/projects/${id}/kg07/interpret/${encodeURIComponent(pertId)}?mode=${mode}${buildId ? `&graph_build_id=${encodeURIComponent(buildId)}` : ''}`, {method:'POST'}),
  kg06Package: (id: string, pertId: string, buildId?: string) => request<Record<string, any>>(`/projects/${id}/kg06/evidence-package/${encodeURIComponent(pertId)}${buildId ? `?graph_build_id=${encodeURIComponent(buildId)}` : ''}`),
  evidence: (id: string, buildId?: string) => request<Record<string, unknown>>(`/evidence/${encodeURIComponent(id)}${buildId ? `?graph_build_id=${encodeURIComponent(buildId)}` : ''}`),
}
