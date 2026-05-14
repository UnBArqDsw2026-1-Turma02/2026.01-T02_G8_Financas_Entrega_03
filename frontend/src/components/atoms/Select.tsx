import type { SelectHTMLAttributes } from 'react'
import './atoms.css'

export interface SelectOption {
  value: string
  label: string
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[]
  placeholder?: string
}

export function Select({ options, placeholder, className, ...rest }: SelectProps) {
  return (
    <select {...rest} className={`atom-select ${className ?? ''}`.trim()}>
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  )
}
