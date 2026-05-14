import type { ReactNode } from 'react'
import './atoms.css'

export type BadgeTone =
  | 'default'
  | 'success'
  | 'danger'
  | 'warning'
  | 'info'
  | 'purple'

export type BadgeVariant = 'solid' | 'outline'

export interface BadgeProps {
  tone?: BadgeTone
  variant?: BadgeVariant
  children: ReactNode
  style?: React.CSSProperties
}

export function Badge({
  tone = 'default',
  variant = 'solid',
  children,
  style,
}: BadgeProps) {
  const toneClass = tone === 'default' ? '' : `atom-badge--${tone}`
  const variantClass = variant === 'outline' ? 'atom-badge--outline' : ''
  return (
    <span
      className={`atom-badge ${variantClass} ${toneClass}`.trim()}
      style={style}
    >
      {children}
    </span>
  )
}
