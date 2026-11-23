import { lazy, Suspense, useEffect, useState } from 'react'
import { Button, Drawer } from 'antd'
import { MenuOutlined } from '@ant-design/icons'
import { Navigate, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api, Project } from './api'
import { ActiveProjectContext, Loading } from './projectContext'
import { projectLabel, zhCN } from './locales/zh-CN'

const Dashboard = lazy(() => import('./pages/DashboardPage'))
const RunComparisonPage = lazy(() => import('./pages/RunComparisonPage'))
const S1Page = lazy(() => import('./pages/S1Page'))
const S2Page = lazy(() => import('./pages/S2Page'))
const GraphPage = lazy(() => import('./pages/GraphPage'))
const RobustResultsPage = lazy(() => import('./pages/RobustResultsPage'))
const DrugPage = lazy(() => import('./pages/DrugPage'))
const ProjectDialogs = lazy(() => import('./components/ProjectDialogs'))

function Navigation({ onNavigate }: { onNavigate?: () => void }) {
  return <nav className="sidebar-nav" aria-label="主导航">
    {zhCN.navigation.map((item) => <NavLink key={item.to} to={item.to} end={'end' in item && item.end} onClick={onNavigate} className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
      <span className="sidebar-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span>
    </NavLink>)}
  </nav>
}

function Brand() {
  return <div className="brand"><div className="brand-mark">DG</div><div><strong>DiseaseGraph</strong><small>科研分析平台</small></div></div>
}

function App() {
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: api.projects })
  const [activeProjectId, setActiveProjectId] = useState<string>()
  const [createProjectOpen, setCreateProjectOpen] = useState(false)
  const [datasetUploadOpen, setDatasetUploadOpen] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const location = useLocation()
  const project = projectsQuery.data?.find((item) => item.project_id === activeProjectId) ?? projectsQuery.data?.[0]
  useEffect(() => setMobileNavOpen(false), [location.pathname])

  const onProjectCreated = (created: Project) => setActiveProjectId(created.project_id)

  return <ActiveProjectContext.Provider value={[project?.project_id, setActiveProjectId]}>
    <div className="shell">
      <aside className="sider"><Brand /><Navigation /><div className="sider-footer">仅显示已登记的研究数据</div></aside>
      <div className="shell-main">
        <header className="topbar">
          <div className="topbar-start">
            <Button className="mobile-menu-button" aria-label="打开导航菜单" icon={<MenuOutlined />} onClick={() => setMobileNavOpen(true)} />
            <div className="project-controls">
              <label htmlFor="active-project">当前项目</label>
              <select id="active-project" className="project-select" aria-label="选择当前项目" value={project?.project_id ?? ''} onChange={(event) => setActiveProjectId(event.target.value)} disabled={projectsQuery.isLoading || !projectsQuery.data?.length}>
                {!projectsQuery.data?.length && <option value="">{projectsQuery.isLoading ? '正在读取项目…' : '暂无项目'}</option>}
                {(projectsQuery.data ?? []).map((item: Project) => <option key={item.project_id} value={item.project_id}>{projectLabel(item.name, item.slug)}</option>)}
              </select>
              <button className="toolbar-button" type="button" onClick={() => setCreateProjectOpen(true)}>新建项目</button>
              <button className="toolbar-button primary" type="button" disabled={!project} onClick={() => setDatasetUploadOpen(true)}>上传数据</button>
            </div>
          </div>
          <span className="platform-label">{zhCN.pageTitle[location.pathname] ?? '研究工作区'}</span>
        </header>
        <main className="content">
          <div className="route-view" key={location.pathname}><Suspense fallback={<Loading />}>
            <Routes>
              <Route path="/" element={<Dashboard />} /><Route path="/s1" element={<S1Page />} />
              <Route path="/s2" element={<S2Page />} /><Route path="/graph" element={<GraphPage />} />
              <Route path="/top10-mechanisms" element={<RobustResultsPage />} />
              <Route path="/formal-top10-m0" element={<Navigate to="/top10-mechanisms" replace />} />
              <Route path="/drugs" element={<DrugPage />} />
              <Route path="/final-results" element={<Navigate to="/top10-mechanisms" replace />} />
              <Route path="/legacy-final-results" element={<Navigate to="/top10-mechanisms" replace />} />
              <Route path="/compare" element={<RunComparisonPage />} /><Route path="*" element={<Dashboard />} />
            </Routes>
          </Suspense></div>
          <footer className="footer">DiseaseGraph Lab · 数据来源与分析版本详见项目报告</footer>
        </main>
      </div>
      <Drawer className="mobile-drawer" placement="left" width={280} title={<Brand />} open={mobileNavOpen} onClose={() => setMobileNavOpen(false)}>
        <Navigation onNavigate={() => setMobileNavOpen(false)} /><div className="sider-footer">仅显示已登记的研究数据</div>
      </Drawer>
      {(createProjectOpen || datasetUploadOpen) && <Suspense fallback={<Loading />}>
        <ProjectDialogs project={project} createOpen={createProjectOpen} uploadOpen={datasetUploadOpen} onCloseCreate={() => setCreateProjectOpen(false)} onCloseUpload={() => setDatasetUploadOpen(false)} onProjectCreated={onProjectCreated} />
      </Suspense>}
    </div>
  </ActiveProjectContext.Provider>
}

export default App
