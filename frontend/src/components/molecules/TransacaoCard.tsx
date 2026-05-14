import type { ReactNode } from 'react'
import { Button } from '../atoms/Button'
import './molecules.css'

export type TransacaoFlow = 'income' | 'outcome'

export interface TransacaoCardProps {
  titulo: string
  valor: string
  fluxo: TransacaoFlow
  data?: string
  meta?: ReactNode
  onEdit?: () => void
  onDelete?: () => void
}

function formatCurrency(value: string): string {
  const n = Number(value)
  if (Number.isNaN(n)) return value
  return n.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

function formatDate(value?: string): string | null {
  if (!value) return null
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString('pt-BR')
}

export function TransacaoCard({
  titulo,
  valor,
  fluxo,
  data,
  meta,
  onEdit,
  onDelete,
}: TransacaoCardProps) {
  const valorClass =
    fluxo === 'income'
      ? 'molecule-transacao-card__value molecule-transacao-card__value--income'
      : 'molecule-transacao-card__value molecule-transacao-card__value--outcome'
  const formattedDate = formatDate(data)
  const sign = fluxo === 'income' ? '+' : '-'
  return (
    <article className="molecule-transacao-card">
      <div className="molecule-transacao-card__main">
        <span className="molecule-transacao-card__title">{titulo}</span>
        <span className="molecule-transacao-card__meta">
          {formattedDate && <span>{formattedDate}</span>}
          {meta}
        </span>
      </div>
      <span className={valorClass}>
        {sign} {formatCurrency(valor)}
      </span>
      <div className="molecule-transacao-card__actions">
        {onEdit && (
          <Button variant="secondary" onClick={onEdit}>
            Editar
          </Button>
        )}
        {onDelete && (
          <Button variant="danger" onClick={onDelete}>
            Excluir
          </Button>
        )}
      </div>
    </article>
  )
}
