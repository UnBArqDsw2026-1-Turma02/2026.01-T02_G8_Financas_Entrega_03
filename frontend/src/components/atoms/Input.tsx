import type { InputHTMLAttributes } from 'react'
import './atoms.css'

export type InputProps = InputHTMLAttributes<HTMLInputElement>

export function Input(props: InputProps) {
  const { className, ...rest } = props
  return <input {...rest} className={`atom-input ${className ?? ''}`.trim()} />
}
