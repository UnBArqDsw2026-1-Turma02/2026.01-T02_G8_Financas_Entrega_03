import type { ButtonHTMLAttributes } from 'react'
import './atoms.css'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
}

export function Button({ variant = 'primary', className, ...rest }: ButtonProps) {
  const variantClass = variant === 'primary' ? '' : `atom-button--${variant}`
  return (
    <button
      type="button"
      {...rest}
      className={`atom-button ${variantClass} ${className ?? ''}`.trim()}
    />
  )
}
