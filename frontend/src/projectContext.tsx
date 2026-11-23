import { createContext, useContext } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from './api'

export const ActiveProjectContext = createContext<[string | undefined, (id: string) => void]>([undefined, () => undefined])

export function useProject() {
  const query = useQuery({ queryKey: ['projects'], queryFn: api.projects })
  const [activeProjectId] = useContext(ActiveProjectContext)
  const project = query.data?.find((p) => p.project_id === activeProjectId) ?? query.data?.[0]
  return { ...query, project }
}

export function Loading({ error }: { error?: Error | null }) {
  if (error) return <div className="page-error" role="alert"><strong>接口读取失败</strong><p>{error.message}</p></div>
  return <div className="loading" role="status" aria-label="加载中"><span className="loading-spinner" /></div>
}
