import { useRef, type ChangeEvent } from 'react'
import './atoms.css'

export interface ColorPickerProps {
  value: string
  onChange: (value: string) => void
  id?: string
  required?: boolean
}

export function ColorPicker({ value, onChange, id, required }: ColorPickerProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const current = value || '#FFFFFF'

  function handle(e: ChangeEvent<HTMLInputElement>) {
    onChange(e.target.value)
  }

  return (
    <div
      className="atom-color-picker"
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
    >
      <span
        className="atom-color-picker__swatch"
        style={{ background: current }}
        aria-hidden="true"
      />
      <span className="atom-color-picker__hex">{current.toUpperCase()}</span>
      <input
        ref={inputRef}
        id={id}
        type="color"
        value={current}
        onChange={handle}
        required={required}
        className="atom-color-picker__input"
        aria-label="Selecionar cor"
      />
    </div>
  )
}
