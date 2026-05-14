import { useMemo } from 'react'

export interface DonutSlice {
  label: string
  value: number
  color: string
}

export interface DonutChartProps {
  data: DonutSlice[]
  size?: number
  thickness?: number
  emptyLabel?: string
}

interface Arc {
  d: string
  color: string
}

function polar(cx: number, cy: number, r: number, angle: number) {
  return {
    x: cx + r * Math.cos(angle),
    y: cy + r * Math.sin(angle),
  }
}

function arcPath(
  cx: number,
  cy: number,
  outerR: number,
  innerR: number,
  start: number,
  end: number,
): string {
  const largeArc = end - start > Math.PI ? 1 : 0
  const startOuter = polar(cx, cy, outerR, start)
  const endOuter = polar(cx, cy, outerR, end)
  const startInner = polar(cx, cy, innerR, end)
  const endInner = polar(cx, cy, innerR, start)
  return [
    `M ${startOuter.x} ${startOuter.y}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 1 ${endOuter.x} ${endOuter.y}`,
    `L ${startInner.x} ${startInner.y}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 0 ${endInner.x} ${endInner.y}`,
    'Z',
  ].join(' ')
}

export function DonutChart({
  data,
  size = 180,
  thickness = 28,
  emptyLabel = 'Sem dados',
}: DonutChartProps) {
  const total = data.reduce((acc, d) => acc + d.value, 0)
  const cx = size / 2
  const cy = size / 2
  const outerR = size / 2 - 2
  const innerR = outerR - thickness

  const arcs = useMemo<Arc[]>(() => {
    if (total <= 0) return []
    // start at top (-90deg)
    let start = -Math.PI / 2
    return data.map((slice) => {
      const angle = (slice.value / total) * Math.PI * 2
      const end = start + angle
      const d = arcPath(cx, cy, outerR, innerR, start, end)
      start = end
      return { d, color: slice.color }
    })
  }, [data, total, cx, cy, outerR, innerR])

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      role="img"
      aria-label="Gráfico de gastos por categoria"
    >
      {total <= 0 ? (
        <>
          <circle
            cx={cx}
            cy={cy}
            r={outerR}
            fill="none"
            stroke="#ececf2"
            strokeWidth={thickness}
          />
          <text
            x={cx}
            y={cy}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={12}
            fill="#a1a1aa"
          >
            {emptyLabel}
          </text>
        </>
      ) : (
        arcs.map((arc, i) => (
          <path key={i} d={arc.d} fill={arc.color} />
        ))
      )}
    </svg>
  )
}
