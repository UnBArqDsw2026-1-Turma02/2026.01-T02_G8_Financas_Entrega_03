import { useEffect, type ReactNode } from 'react'
import './organisms.css'

export interface ModalProps {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
}

function CloseIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M6 6l12 12" />
      <path d="M18 6l-12 12" />
    </svg>
  )
}

export function Modal({ open, title, onClose, children }: ModalProps) {
  useEffect(() => {
    if (!open) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="organism-modal-backdrop" onClick={onClose}>
      <div
        className="organism-modal"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="organism-modal__header">
          <h2 className="organism-modal__title">{title}</h2>
          <button
            type="button"
            className="organism-modal__close"
            aria-label="Fechar"
            onClick={onClose}
          >
            <CloseIcon />
          </button>
        </header>
        {children}
      </div>
    </div>
  )
}
