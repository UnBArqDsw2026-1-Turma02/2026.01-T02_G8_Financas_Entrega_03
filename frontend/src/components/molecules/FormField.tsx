import { useId, type ReactElement, type ReactNode, cloneElement } from 'react'
import './molecules.css'

export interface FormFieldProps {
  label: string
  error?: string | null
  hint?: ReactNode
  children: ReactElement<{ id?: string }>
}

export function FormField({ label, error, hint, children }: FormFieldProps) {
  const reactId = useId()
  const childId = children.props.id ?? reactId
  const child = cloneElement(children, { id: childId })
  return (
    <div className="molecule-form-field">
      <label className="molecule-form-field__label" htmlFor={childId}>
        {label}:
      </label>
      {child}
      {hint && !error && <span className="molecule-form-field__hint">{hint}</span>}
      {error && <span className="molecule-form-field__error">{error}</span>}
    </div>
  )
}
