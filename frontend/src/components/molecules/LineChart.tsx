import { useMemo } from 'react'

export interface LinePoint {
  label: string
  value: number
}

export interface LineChartProps {
  data: LinePoint[]
  width?: number
  height?: number
  color?: string
  emptyLabel?: string
}

const PADDING = { top: 16, right: 16, bottom: 28, left: 44 }

function niceMax(value: number): number {
  if (value <= 0) return 100
  const pow = Math.pow(10, Math.floor(Math.log10(value)))
  const norm = value / pow
  let nice: number
  if (norm <= 1) nice = 1
  else if (norm <= 2) nice = 2
  else if (norm <= 5) nice = 5
  else nice = 10
  return nice * pow
}

export function LineChart({
  data,
  width = 520,
  height = 220,
  color = '#4F378A',
  emptyLabel = 'Sem dados',
}: LineChartProps) {
  const { points, ticks, plotW } = useMemo(() => {
    const plotW = width - PADDING.left - PADDING.right
    const plotH = height - PADDING.top - PADDING.bottom
    const maxRaw = data.reduce((m, p) => (p.value > m ? p.value : m), 0)
    const maxY = niceMax(maxRaw)
    const stepX = data.length > 1 ? plotW / (data.length - 1) : 0
    const points = data.map((p, i) => {
      const x = PADDING.left + i * stepX
      const y =
        PADDING.top + (maxY > 0 ? plotH - (p.value / maxY) * plotH : plotH)
      return { x, y, ...p }
    })
    const ticks = [0, 0.25, 0.5, 0.75, 1].map((r) => ({
      y: PADDING.top + plotH - r * plotH,
      value: maxY * r,
    }))
    return { points, ticks, plotW }
  }, [data, width, height])

  if (data.length === 0) {
    return (
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
      >
        <text
          x={width / 2}
          y={height / 2}
          textAnchor="middle"
          fontSize={12}
          fill="#a1a1aa"
        >
          {emptyLabel}
        </text>
      </svg>
    )
  }

  const linePath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ')

  const labelEvery = Math.max(1, Math.ceil(data.length / 6))

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Tendência de gastos"
    >
      {ticks.map((t, i) => (
        <g key={i}>
          <line
            x1={PADDING.left}
            x2={PADDING.left + plotW}
            y1={t.y}
            y2={t.y}
            stroke="#f1eefb"
            strokeWidth={1}
          />
          <text
            x={PADDING.left - 8}
            y={t.y}
            textAnchor="end"
            dominantBaseline="central"
            fontSize={10}
            fill="#a1a1aa"
          >
            {Math.round(t.value)}
          </text>
        </g>
      ))}
      <path d={linePath} fill="none" stroke={color} strokeWidth={2} />
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={2.5} fill={color} />
      ))}
      {points.map((p, i) =>
        i % labelEvery === 0 ? (
          <text
            key={`lbl-${i}`}
            x={p.x}
            y={height - 8}
            textAnchor="middle"
            fontSize={10}
            fill="#a1a1aa"
          >
            {p.label}
          </text>
        ) : null,
      )}
    </svg>
  )
}
