import type { CSSProperties } from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import { use } from 'echarts/core'
import { BarChart, LineChart, ScatterChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import * as echarts from 'echarts/core'
import { chartPalette } from './designTokens'

use([BarChart, LineChart, ScatterChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

export default function ChartRenderer({ option, style }: { option: any; style?: CSSProperties }) {
  const themedOption = {
    ...option,
    color: option.color ?? chartPalette,
    textStyle: { fontFamily: '-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif', color: '#45454b', ...option.textStyle },
    animationDuration: option.animationDuration ?? 220,
    tooltip: { backgroundColor: 'rgba(29,29,31,.94)', borderWidth: 0, textStyle: { color: '#fff', fontSize: 12 }, padding: [9, 12], ...option.tooltip },
  }
  return <ReactEChartsCore echarts={echarts} option={themedOption} style={style} notMerge lazyUpdate opts={{ renderer: 'canvas' }} />
}
