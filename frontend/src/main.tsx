import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import antdZhCN from 'antd/locale/zh_CN'
import { palette } from './designTokens'
import App from './App'
import 'antd/dist/reset.css'
import './styles.css'

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: 1 } } })

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><ConfigProvider locale={antdZhCN} theme={{
    token: { colorPrimary: palette.primary, colorText: palette.ink, colorTextSecondary: palette.muted, colorBgLayout: '#f5f5f7', colorBorderSecondary: '#e8e8ed', borderRadius: 12, controlHeight: 40, fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif' },
    components: { Card: { headerBg: '#fff' }, Table: { headerBg: '#f7f7f9', rowHoverBg: '#f6faff' }, Modal: { borderRadiusLG: 20 }, Drawer: { borderRadiusLG: 20 } },
  }}><QueryClientProvider client={queryClient}><BrowserRouter><App /></BrowserRouter></QueryClientProvider></ConfigProvider></React.StrictMode>,
)
