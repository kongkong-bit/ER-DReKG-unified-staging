export const palette = {
  primary: '#2878d0', ink: '#1d1d1f', muted: '#6e6e73', subtle: '#8291a6',
  accentWash: '#f2f7fb', neutral: '#a9b4c2', grid: '#edf0f4',
  up: '#d97563', down: '#4b83c5', success: '#52a487', threshold: '#7f8b99',
  graph: {
    node: '#6683b4', drug: '#df8c64', pathway: '#57a68a', candidate: '#d5aa4e',
    text: '#23324a', edge: '#c0c8d3', arrow: '#aeb9c7', edgeText: '#696970',
    directEdge: '#4c83bd', associationEdge: '#8b96a5', mechanismEdge: '#b58a46', pathwayEdge: '#8e74bf', expressionEdge: '#4b83c5',
    highlight: '#d14f60', highlightBorder: '#8e2534',
  },
} as const

export const chartPalette = [palette.primary, '#4e9b83', '#d58a52', '#9a82c5', '#bd626c', '#69a8a1'] as const
