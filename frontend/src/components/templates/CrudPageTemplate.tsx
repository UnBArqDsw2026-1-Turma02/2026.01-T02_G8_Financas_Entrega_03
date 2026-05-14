import type { ReactNode } from 'react'
import { PlusIcon } from '../atoms/Icon'
import './crud-page.css'

export interface CrudPageTemplateProps {
  title: string
  isLoading?: boolean
  error?: string | null
  onCreate?: () => void
  createLabel?: string
  children: ReactNode
}

export function CrudPageTemplate({
  title,
  isLoading,
  error,
  onCreate,
  createLabel = 'Novo',
  children,
}: CrudPageTemplateProps) {
  return (
    <section className="crud-page">
      <header className="crud-page__header">
        <h1 className="crud-page__title">{title}</h1>
        {onCreate && (
          <button type="button" className="crud-page__create" onClick={onCreate}>
            <PlusIcon />
            <span>{createLabel}</span>
          </button>
        )}
      </header>
      {error && <div className="crud-page__error">{error}</div>}
      <div className="crud-page__card">
        {isLoading ? (
          <div className="crud-page__loading">Carregando…</div>
        ) : (
          children
        )}
      </div>
    </section>
  )
}
