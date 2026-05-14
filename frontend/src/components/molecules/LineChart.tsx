import { useId, useMemo, useState } from 'react'

export interface LinePoint {
  label: string
  value: number
  tooltipLabel?: string
}

export interface LineChartProps {
  data: LinePoint[]
  width?: number
  height?: number
  color?: string
  emptyLabel?: string
  formatValue?: (value: number) => string
}

const PADDING = { top: 20, right: 24, bottom: 32, left: 56 }

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

function defaultFormat(value: number): string {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  })
}

export function LineChart({
  data,
  width = 560,
  height = 240,
  color = '#4F378A',
  emptyLabel = 'Sem dados',
  formatValue = defaultFormat,
}: LineChartProps) {
  const gradientId = useId()
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)

  const { points, ticks, plotW, plotH } = useMemo(() => {
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
    return { points, ticks, plotW, plotH }
  }, [data, width, height])

  if (data.length === 0) {
    return (
      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
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

  const areaPath =
    points.length > 0
      ? `${linePath} L ${points[points.length - 1].x} ${
          PADDING.top + plotH
        } L ${points[0].x} ${PADDING.top + plotH} Z`
      : ''

  const labelEvery = Math.max(1, Math.ceil(data.length / 6))
  const hovered = hoverIndex !== null ? points[hoverIndex] : null

  // Tooltip box dimensions (in SVG units)
  const tooltipW = 130
  const tooltipH = 44
  let tooltipX = 0
  let tooltipY = 0
  if (hovered) {
    tooltipX = hovered.x - tooltipW / 2
    tooltipY = hovered.y - tooltipH - 12
    const minX = PADDING.left
    const maxX = PADDING.left + plotW - tooltipW
    if (tooltipX < minX) tooltipX = minX
    if (tooltipX > maxX) tooltipX = maxX
    if (tooltipY < PADDING.top - 8) {
      tooltipY = hovered.y + 14
    }
  }

  return (
    <svg
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Tendência de gastos"
      onMouseLeave={() => setHoverIndex(null)}
      style={{ display: 'block' }}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.22} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>

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
            x={PADDING.left - 10}
            y={t.y}
            textAnchor="end"
            dominantBaseline="central"
            fontSize={11}
            fill="#a1a1aa"
          >
            {formatValue(t.value)}
          </text>
        </g>
      ))}

      <path d={areaPath} fill={`url(#${gradientId})`} />
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {points.map((p, i) =>
        i % labelEvery === 0 ? (
          <text
            key={`lbl-${i}`}
            x={p.x}
            y={height - 10}
            textAnchor="middle"
            fontSize={11}
            fill="#a1a1aa"
          >
            {p.label}
          </text>
        ) : null,
      )}

      {points.map((p, i) => {
        const isHovered = hoverIndex === i
        return (
          <circle
            key={`pt-${i}`}
            cx={p.x}
            cy={p.y}
            r={isHovered ? 5 : 3}
            fill={isHovered ? '#ffffff' : color}
            stroke={color}
            strokeWidth={isHovered ? 2.5 : 1}
          />
        )
      })}

      {/* Invisible hover targets — wider, so it's easy to land on a point */}
      {points.map((p, i) => {
        const half =
          points.length > 1 ? (plotW / (points.length - 1)) / 2 : plotW / 2
        return (
          <rect
            key={`hit-${i}`}
            x={p.x - half}
            y={PADDING.top}
            width={Math.max(half * 2, 4)}
            height={plotH}
            fill="transparent"
            onMouseEnter={() => setHoverIndex(i)}
            onFocus={() => setHoverIndex(i)}
            onBlur={() => setHoverIndex(null)}
            tabIndex={0}
            style={{ cursor: 'pointer', outline: 'none' }}
          >
            <title>{`${p.tooltipLabel ?? p.label}: ${formatValue(p.value)}`}</title>
          </rect>
        )
      })}

      {hovered && (
        <g pointerEvents="none">
          <line
            x1={hovered.x}
            x2={hovered.x}
            y1={PADDING.top}
            y2={PADDING.top + plotH}
            stroke={color}
            strokeOpacity={0.25}
            strokeDasharray="3 3"
          />
          <rect
            x={tooltipX}
            y={tooltipY}
            width={tooltipW}
            height={tooltipH}
            rx={8}
            ry={8}
            fill="#1f1d2a"
          />
          <text
            x={tooltipX + tooltipW / 2}
            y={tooltipY + 16}
            textAnchor="middle"
            fontSize={11}
            fill="#d4d4d8"
          >
            {hovered.tooltipLabel ?? hovered.label}
          </text>
          <text
            x={tooltipX + tooltipW / 2}
            y={tooltipY + 33}
            textAnchor="middle"
            fontSize={13}
            fontWeight={600}
            fill="#ffffff"
          >
            {formatValue(hovered.value)}
          </text>
        </g>
      )}
    </svg>
  )
}
