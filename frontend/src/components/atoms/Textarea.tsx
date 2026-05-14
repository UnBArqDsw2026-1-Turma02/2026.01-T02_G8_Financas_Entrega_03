import type { TextareaHTMLAttributes } from 'react'
import './atoms.css'

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>

export function Textarea(props: TextareaProps) {
  const { className, ...rest } = props
  return <textarea {...rest} className={`atom-textarea ${className ?? ''}`.trim()} />
}
